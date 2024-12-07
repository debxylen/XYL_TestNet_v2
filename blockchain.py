import hashlib
import json
import time
import os
import pickle
from tx_decode import tx_decode
from crypt_util import ep_save, ep_load
from block import Block
from transaction import Transaction, tx_from_json
from sign import verify_sign
from smartcontract import SmartContract, ContractManager
import traceback
from dotenv import load_dotenv
from utils import *
from errors import *
load_dotenv()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.unconfirmed_transactions = []
        self.balances = {}
        self.u = (10**18)
        self.difficulty = 4
        self.contract_manager = ContractManager(self)  
        self.create_genesis_block()
        if os.path.exists('blockchain'):
            self.load_chain()
        if os.path.exists('balances'):
            self.load_balances()
        if os.path.exists('contract_manager'):
            self.load_contracts()
        print("Network Balance: ", self.balances['network'], "aka", self.balances['network']/(10**18))
        print("NetMiner Balance: ", self.balances.get('network_miner',0), "aka", self.balances.get('network_miner',0)/(10**18))
        self.state = {} 
        self.event_log = []
        self.mining_times =  {}
        
    def get_state(self):
        """Return the current state of the blockchain."""
        return self.state
        
    def update_state(self, contract_address, method_name, result):
        """Update the blockchain state with the result of a smart contract method execution."""
        contract_address = str(contract_address).lower()
        if contract_address not in self.balances:
            self.balances[contract_address] = {}  # Initialize contract state if not exists
        self.balances[contract_address][method_name] = result
        self.save_balances()  # Ensure state is saved after update
        
    def create_genesis_block(self):
        """Generate the first block in the blockchain (the Genesis block)."""
        genesis_block = Block(0, "0", [], 0)
        genesis_block.hash = genesis_block.compute_hash()  # Compute the hash of the genesis block
        self.chain.append(genesis_block)  # Add it to the chain

    def add_transaction(self, sender, recipient, amount: int):
        """Add a new transaction to the list of unconfirmed transactions."""
        sender = sender.lower()
        recipient = recipient.lower()
        amount = int(amount)
        transaction = Transaction(sender, recipient, amount)
        if transaction.is_valid(sender_balance=self.get_balance(sender)):
            self.unconfirmed_transactions.append(transaction)
        else:
            raise InsufficientBalanceError(f"Insufficient funds for transaction: {sender} has {self.get_balance(sender)} but needs {amount}")
            
    def create_new_block(self, transactions=None):
        """Create and add a new block with the current unconfirmed transactions."""
        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            previous_hash=last_block.hash,
            transactions=transactions if transactions else self.unconfirmed_transactions,
            nonce=0  # The miner will find the nonce
        )
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        self.unconfirmed_transactions = []

    def get_last_block(self):
        """Retrieve the most recent block in the chain."""
        return self.chain[-1]

    def get_balance(self, address: str):
        """Retrieve the balance of the given address."""
        return int(self.balances.get(address.lower(), 0))  # Return 0 if address has no balance

    def get_latest_block_times(self, num_blocks=3):
        """Get the start and end times for the latest blocks."""
        # Get the last 'num_blocks' blocks and check if their times are recorded
        latest_blocks = list(self.mining_times.items())[-num_blocks:]
        valid_blocks = []
        
        for block_id, times in latest_blocks:
            if times.get("start") is not None and times.get("end") is not None:
                valid_blocks.append(times)
        
        return valid_blocks

    def adjust_difficulty(self):
        """Adjust the difficulty based on mining times."""
        # Get the latest blocks' mining times (e.g., last 3 blocks)
        recent_blocks = self.get_latest_block_times(num_blocks=3)
        
        if len(recent_blocks) < 2:
            print("Not enough blocks with recorded times. Setting difficulty to default.")
            self.difficulty = 4  # Set to default difficulty if not enough blocks
            return self.difficulty

        # Calculate the average mining time for the recent blocks
        avg_time = sum([block["end"] - block["start"] for block in recent_blocks]) / len(recent_blocks)
        print(f"Average mining time for recent blocks: {avg_time:.2f} seconds.")

        # Adjust difficulty based on the average mining time
        if avg_time < 2:
            self.difficulty += 1  # Increase difficulty if mining was too fast
            print(f"Block mined too quickly ({avg_time:.2f}s), increasing difficulty to {self.difficulty}.")
        elif avg_time > 5:
            self.difficulty -= 1  # Decrease difficulty if mining was too slow
            print(f"Block mined too slowly ({avg_time:.2f}s), decreasing difficulty to {self.difficulty}.")

        # Ensure difficulty stays within bounds
        self.difficulty = max(2, self.difficulty)
        return self.difficulty


    def generate_mining_job(self):
        """Generate a new mining job."""
        if len(self.unconfirmed_transactions) == 0:
            return 'NO_JOB'

        last_block = self.get_last_block()
        # Limit to 5 transactions per mining job
        transactions_to_mine = self.unconfirmed_transactions[:5]

        job = {
            "index": last_block.index + 1,
            "previous_hash": last_block.hash,
            "difficulty": self.difficulty,
            "transactions": [utdict.__json__() for utdict in transactions_to_mine],
        }

        self.mining_times[str(job['index'])] = {}  # Initialize dictionary with key as the index
        self.mining_times[str(job['index'])]['start'] = time.time()  # Record job generation time

        # Remove only the transactions included in this job from the pool
        self.unconfirmed_transactions = self.unconfirmed_transactions[5:]

        return job


    def validate_mined_block(self, block, miner_nonce):
        """Validate the mined block."""
        txs = []
        for i in block['transactions']:
            txs.append(i)
        target = '0' * block['difficulty']  # difficulty: leading zeros in the hash
        block_header = f"{block['previous_hash']}{json.dumps(txs)}{miner_nonce}"
        block_hash = hashlib.sha256(block_header.encode()).hexdigest()
        if not block['hash'] == block_hash:
            return False, block_hash
        # Check if the block hash already exists in the chain
        for block in self.chain:
            if block.hash == block_hash:
                print(f"Duplicate block hash found: {block_hash}")
                return False, block_hash
        return str(block_hash).startswith(target), block_hash      
      
    def submit_mined_block(self, mined_block, miner):
        """Add a mined block to the blockchain."""
        self.mining_times[str(mined_block['index'])]['end'] = time.time()
        self.adjust_difficulty()

        # Validate the mined block
        valid, block_hash = self.validate_mined_block(mined_block, mined_block['nonce'])
        if valid:
            trxs = []
            miner = miner.lower()
            total_gas_collected = 0

            # Set the transaction limit (e.g., 5 transactions per block)
            MAX_TRANSACTIONS = 100
            if len(mined_block['transactions']) > MAX_TRANSACTIONS:
                print(f"Rejected block: contains more than {MAX_TRANSACTIONS} transactions")
                return None

            # Process each transaction in the mined block
            for tx_data in mined_block['transactions']:
                tx = tx_from_json(tx_data)
                trxs.append(tx)

                sender = tx.sender.lower()
                recipient = tx.recipient.lower()
                amount = int(tx.amount)

                # Gas calculations
                amt = find_actual_amount(amount, 0.003469)
                self.update_balance(sender, -amt)  # Deduct amount (including gas) from sender
                self.update_balance(recipient, amount)  # Add amount to recipient (after gas)
                self.update_balance('network', 0.002400 * amt)  # Add gas to network
                total_gas_collected += 0.001069 * amt  # Accumulate gas for miner reward

            # Add miner reward transaction
            trxs.append(Transaction('network', miner, total_gas_collected))

            # Create and append the new block
            new_block = Block(
                index=mined_block['index'],
                previous_hash=mined_block['previous_hash'],
                transactions=trxs,
                nonce=mined_block['nonce']
            )
            new_block.hash = block_hash
            self.chain.append(new_block)

            # Clear unconfirmed transactions that were processed
            self.unconfirmed_transactions = [
                tx for tx in self.unconfirmed_transactions
                if tx.hash not in [tx.hash for tx in trxs]
            ]

            # Save chain and balances
            self.save_chain()
            self.save_balances()

            return new_block
        else:
            print(f'Rejected block {block_hash}')
            return None


    def get_transaction_by_hash(self, tx_hash):
        """Retrieve a transaction by its hash."""
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.tx_hash == tx_hash:
                    tx_data = transaction.__json__()
                    tx_data['blockNumber'] = block.index
                    return tx_data
        return None

    def get_block_by_hash(self, block_hash):
        """Retrieve a block by its hash."""
        for block in self.chain:
            if str(block.hash) == str(block_hash):
                return block
        return None

    def update_balance(self, address, amount: int):
        """Update the balance for the given address."""
        address = address.lower()
        if address in self.balances:
            self.balances[address] += amount
        else:
            self.balances[address] = amount
    
    def send_raw_transaction(self, raw_transaction):
        try:
            tx_dict = tx_decode(raw_transaction)
            if not int(tx_dict['chainId']) == 6934:
                return {"data": f"Invalid transaction: chainId {tx_dict['chainId']} doesn't match 6934."}
            verif = verify_sign(tx_dict)
            if not verif[0]:
                return {'data': 'Invalid transaction.'}

            sender = verif[-1]
            amount = int(tx_dict['value'])
            recipient = tx_dict['to']

            if len(tx_dict.get('data'))>0 and str(recipient)=='None':  # Contract deployment with compiled bytecode
                c_code = tx_dict["data"]
                contract_address = SmartContract(self, sender, c_code).address
                print(f"[LOG] Contract Creation: {contract_address}")
                return {"contractAddress": contract_address}

            elif len(tx_dict.get('data'))>0 and (not str(tx_dict.get('data')) == '0x') and len(recipient)>0 and str(recipient).startswith('0x'):  # Contract execution
                contract_address = recipient.lower()
                data = tx_dict["data"]
                response = self.contract_manager.contracts[contract_address.lower()].execute(self, data, sender)
                print(f"[LOG] Contract Execution: {contract_address} {data}")
                return response

            # Regular transaction
            self.add_transaction(sender, recipient, amount)
            return {
                'blockNumber': len(self.chain),
                'transactionHash': hashlib.sha256(raw_transaction.encode()).hexdigest()
            }

        except Exception as e:
            print(f"Error processing transaction: {traceback.format_exc()}")
            return None
          
    def get_transaction_count(self, address: str):
        address = address.lower()
        count = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.__json__()['sender'] == address:
                    count += 1
        return count

    def save_balances(self):
        ep_save(self.balances, 'balances', os.getenv("KEY"))

    def load_balances(self):
        self.balances = ep_load('balances', os.getenv("KEY"))

    def save_chain(self):
        ep_save(self.chain, 'blockchain', os.getenv("KEY"))

    def load_chain(self):
        self.chain = ep_load('blockchain', os.getenv("KEY"))

    def save_contracts(self):
        ep_save(self.contract_manager, 'contract_manager', os.getenv('CONTRACT_KEY'))

    def load_contracts(self):
        self.contract_manager = ep_load('contract_manager', os.getenv('CONTRACT_KEY'))     
        
    def get_transaction_receipt(self, transaction_id: str):
        """Get the transaction receipt for a specific transaction."""
        for block in self.chain:
            for index, transaction in enumerate(block.transactions):
                if int(block.index) == int(transaction_id):
                    if transaction.amount == 0:
                        gas = int(0.003469 * (10**18))
                    else:
                        gas = int(0.003469 * transaction.amount)
                    return {
                        'blockHash': block.hash,
                        'blockNumber': hex(block.index),
                        'contractAddress': None,
                        'cumulativeGasUsed': hex(gas),
                        'effectiveGasPrice': hex(1),
                        'from': transaction.sender,
                        'gasUsed': hex(gas),
                        'status': hex(1),
                        'to': transaction.recipient,
                        'transactionHash': transaction.tx_hash,
                        'transactionIndex': hex(index),
                        'type': 0,
                        'amount': hex(transaction.amount),
                    }
        raise TransactionNotFoundError(f"Transaction not found with ID {transaction_id}")

