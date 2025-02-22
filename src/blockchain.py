import hashlib
import json
import time
import os
import pickle
from pymongo.mongo_client import MongoClient
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

db_pass = os.getenv("DB_PASSWORD")
mongo_url = f"mongodb+srv://priyanshudeb3:{db_pass}@maincluster.g1xdb.mongodb.net/?retryWrites=true&w=majority&appName=MainCluster"

class Blockchain:
    def __init__(self):
        self.mongo_client = MongoClient(mongo_url)
        self.db = self.mongo_client['XYL_TestNet']
        self.chain = []
        self.unconfirmed_transactions = []
        self.balances = {}
        self.u = (10**18)
        self.difficulty = 4
        self.contract_manager = ContractManager(self)  
        if os.path.exists('blockchain'):
            self.load_chain()
        else:
            self.create_genesis_block()
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
        if contract_address not in self.state:
            self.state[contract_address] = {}  # Initialize contract state if not exists
        self.state[contract_address][method_name] = result
        
    def create_genesis_block(self):
        """Generate the first block in the blockchain (the Genesis block)."""
        genesis_block = Block(0, "0", [], 0)
        genesis_block.hash = genesis_block.compute_hash()  # Compute the hash of the genesis block
        self.chain.append(genesis_block)  # Add it to the chain
        self.db['chain'].insert_one(genesis_block.__json__())

    def add_transaction(self, sender, recipient, amount: int, nonce = None):
        """Add a new transaction to the list of unconfirmed transactions."""
        sender = sender.lower()
        recipient = recipient.lower()
        amount = int(amount)
        if nonce == None:
            nonce = self.get_transaction_count(sender)
        transaction = Transaction(sender, recipient, amount, nonce)
        if transaction.is_valid(sender_balance=self.get_balance(sender)):
            self.unconfirmed_transactions.append(transaction)
        else:
            raise InsufficientBalanceError(f"Insufficient funds for transaction: {sender} has {self.get_balance(sender)} but needs {amount}")

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

        transactions_to_mine = self.unconfirmed_transactions[:10]

        job = {
            "index": last_block.index + 1,
            "previous_hash": last_block.hash,
            "difficulty": self.difficulty,
            "transactions": [utdict.__json__() for utdict in transactions_to_mine],
        }

        self.mining_times[str(job['index'])] = {}  # Initialize dictionary with key as the index
        self.mining_times[str(job['index'])]['start'] = time.time()  # Record job generation time

        # Remove only the transactions included in this job from the pool
        # self.unconfirmed_transactions = self.unconfirmed_transactions[10:]

        return job

    def validate_mined_block(self, block, miner_nonce):
        """Validate the mined block."""
        V1 = block['index'] == self.chain[-1].index + 1
        V2 = block['previous_hash'] == self.chain[-1].hash

        if not (V1 and V2):
            return False, block['hash'], "Block already mined."

        txs = []
        for i in block['transactions']:
            txs.append(i)
        target = '0' * block['difficulty']  # difficulty: leading zeros in the hash
        block_header = f"{block['previous_hash']}{json.dumps(txs)}{miner_nonce}"

        # Use hashlib.blake2b for hashing
        block_hash = hashlib.blake2b(block_header.encode(), digest_size=64).hexdigest()

        if not block['hash'] == block_hash:
            return False, block_hash, f"Given hash doesn't match expected hash for nonce {miner_nonce}."

        # Check if the block hash already exists in the chain
        for chain_block in self.chain:
            if chain_block.hash == block_hash:
                return False, block_hash, f"Duplicate block hash found: {block_hash}"

        return block_hash.startswith(target), block_hash, "Block is valid."

      
    def submit_mined_block(self, mined_block, miner):
        """Add a mined block to the blockchain."""
        self.mining_times[str(mined_block['index'])]['end'] = time.time()
        self.adjust_difficulty()

        # Validate the mined block
        valid, block_hash, reason = self.validate_mined_block(mined_block, mined_block['nonce'])
        if valid:
            trxs = []
            miner = miner.lower()
            total_gas_collected = 0

            # Set the transaction limit (e.g., 5 transactions per block)
            MAX_TRANSACTIONS = 10 
            if len(mined_block['transactions']) > MAX_TRANSACTIONS:
                print(f"Rejected block: contains more than {MAX_TRANSACTIONS} transactions")
                return None

            # Process each transaction in the mined block
            for tx_data in mined_block['transactions']:
                tx = tx_from_json(tx_data)

                sender = tx.sender.lower()
                recipient = tx.recipient.lower()
                amount = int(tx.amount)

                try: # clear processed tx before +/- the stuff
                    for unconfirmed_tx in self.unconfirmed_transactions:
                        if unconfirmed_tx.tx_hash == tx.tx_hash:
                            self.unconfirmed_transactions.remove(unconfirmed_tx)
                    # self.unconfirmed_transactions.remove(tx)
                    # print("Removed transaction from unconfirmed list: ", tx.tx_hash)
                except ValueError: # if it couldnt be removed from unconfirmed txs, means its already mined and added, so dont add again
                    # print(f"Transaction already mined: {tx.tx_hash}")
                    continue # move to next transaction
                
                # Gas calculations
                if amount == 0:
                    print(f"0 transaction found: {tx}")
                    amt = find_actual_amount(amount, 0.003469)
                    if self.get_balance(sender) < 0.003469:  # Ensure sender can afford base gas fee
                        print(f"Rejected transaction with hash {tx.tx_hash}: Not enough balance.")
                        continue  # Skip this transaction, do not add to the block
                    self.update_balance(sender, -0.003469)  # base fee to discourage 0-tx
                    self.update_balance(recipient, 0)  # 0 value tx so recipient gets none
                    self.update_balance('network', 0.001400)  # Add gas to network
                    total_gas_collected += 0.002069  # Accumulate gas for miner reward
                else:
                    # Gas calculations
                    amt = find_actual_amount(amount, 0.003469)
                    if self.get_balance(sender) < amt:  # Ensure sender can afford gas fee + amount to send
                        print(f"Rejected transaction with hash {tx.tx_hash}: Not enough balance.")
                        continue  # Skip this transaction, do not add to the block
                    self.update_balance(sender, -amt)  # Deduct amount (including gas) from sender
                    self.update_balance(recipient, amount)  # Add amount to recipient (after gas)
                    self.update_balance('network', 0.001400 * amt)  # Add gas to network
                    total_gas_collected += 0.002069 * amt  # Accumulate gas for miner reward
                    
                trxs.append(tx) # append to txrs once all +/- is done
                
            if not (len(trxs) > 0):
                return None, "No transactions were added to chain, either because all of them are already mined, or are invalid."

            # Add miner reward transaction
            trxs.append(Transaction('network', miner, total_gas_collected, 0))

            # Create and append the new block
            new_block = Block(
                index=mined_block['index'],
                previous_hash=mined_block['previous_hash'],
                transactions=trxs,
                nonce=mined_block['nonce']
            )
            new_block.hash = block_hash
            self.chain.append(new_block)
            new_block_for_db = new_block.__json__()
            for dbtx in new_block_for_db['transactions']:
                dbtx['amount'] = str(dbtx['amount'])
            self.db['chain'].insert_one(new_block_for_db)

            # Clear unconfirmed transactions that were processed
            # self.unconfirmed_transactions = [
            #    tx for tx in self.unconfirmed_transactions
            #    if tx.hash not in [tx.hash for tx in trxs]
            # ]

            # Save chain and balances
            self.save_chain()
            self.save_balances()

            return new_block, "Block accepted and added to chain."
        else:
            return None, f'Rejected block {block_hash}: {reason}'


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
        self.db['balances'].update_one(
            {"address": address},  # Query: Find the document for the address
            {"$set": {"balance": str(self.balances[address])}},  # Sync with balance in blockchain
            upsert=True  # Create a new document if it doesn't exist
        )

    def find_pending(self, sender, nonce):
        for tx in self.unconfirmed_transactions:
            if tx.sender.lower() == sender.lower() and int(tx.nonce) == int(nonce):
                return tx
        return None

    def send_raw_transaction(self, raw_transaction):
        try:
            tx_dict = tx_decode(raw_transaction)

            if not int(tx_dict['chainId']) == 6934:
                return {"error": f"Invalid transaction: chainId {tx_dict['chainId']} doesn't match 6934."}

            if (tx_dict['gas'] < tx_dict['value']*0.003469) or (tx_dict['gasPrice']!=1):
                return {'error': 'Invalid gas values provided.'}

            if int(tx_dict['value']) < 1000000 and int(tx_dict['value']) != 0:
                return {'error': f"Rejected transaction: Minimum transaction amount is 1,000,000 wxei for non-zero transactions."}              

            verif = verify_sign(tx_dict) # makes sure that its signed by the sender by reconstructing address and comparing with given address
            if not verif[0]:
                return {'error': 'Invalid transaction.'}
            sender = verif[-1]
            amount = round_to_valid_amount(int(tx_dict['value']))
            amount = amount - (amount*0.003469)
            nonce = int(tx_dict['nonce'])
            recipient = tx_dict['to']              

            if not nonce == self.get_transaction_count(sender.lower()):
                return {'error': 'Invalid nonce provided.'}

            if self.get_balance(sender) < find_actual_amount(amount, 0.003469):  # Ensure sender can afford gas fee as well as sending value
                return {'error': f"Rejected transaction: Not enough balance."}

            if self.get_balance(sender) < 0.003469: # ensuring enough balance for gas to avoid problems later
                return {'error': f'Not enough balance to pay for gas: 0.003469 is the minimum total gas cost, sender has {self.get_balance(sender)}'}

            if amount == 0 and sender.lower() == recipient.lower(): # cancel tx
                to_cancel = self.find_pending(sender, nonce) # tx to cancel
                if to_cancel: # if there is a cancellable one
                    try:
                        self.unconfirmed_transactions.remove(to_cancel) # remove from unconfirmed tx
                    except ValueError:
                        return {'error': 'Transaction not found or already mined.'} # checked again, if it couldnt be removed due to tx not being in unconfrmed list, means its mined in meantime, so dont proceed
                    self.add_transaction(sender, sender, 0, nonce) # add the transaction with same sender and recipient, 0 amt, and given nonce
                    return {
                        'blockNumber': len(self.chain),
                        'transactionHash': hashlib.sha256(raw_transaction.encode()).hexdigest()
                    }
                return {'error': 'Transaction not found or already mined.'}

            if len(tx_dict.get('data'))>0 and str(recipient)=='None':  # Contract deployment with compiled bytecode
                c_code = tx_dict["data"]
                contract_address = SmartContract(self, sender, c_code).address
                self.db['contracts'].insert_one({"contract_address": contract_address.lower(), "code": c_code, "owner": sender.lower()})
                print(f"[LOG] Contract Creation: {contract_address}")
                return {"contractAddress": contract_address}

            elif len(tx_dict.get('data'))>0 and (not str(tx_dict.get('data')) == '0x') and len(recipient)>0 and str(recipient).startswith('0x'):  # Contract execution
                contract_address = recipient.lower()
                data = tx_dict["data"]
                response = self.contract_manager.contracts[contract_address.lower()].execute(self, data, sender)
                print(f"[LOG] Contract Execution: {contract_address} {data}")
                return response

            # Regular transaction
            self.add_transaction(sender, recipient, amount, nonce)
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
        try:
            balances = {}
            bals = self.db['balances'].find().sort("address", 1)
            for i in bals:
                address = i.get("address")
                amount = i.get("amount")
                try:
                    balances[address.lower()] = int(float(amount))
                except:
                    balances[address.lower()] = float(amount)
            self.balances = balances
            print("Loaded balances from cloud database.")
        except:
            print(traceback.format_exc())
            self.balances = ep_load('balances', os.getenv("KEY"))
            print("Couldn't load balances from cloud, loaded from local file. ")
            
    def save_chain(self):
        ep_save(self.chain, 'blockchain', os.getenv("KEY"))

    def load_chain(self):
        # Get all entries from the collection
        try:
            entries = self.db['chain'].find().sort("index", 1)

            # List to store Block objects
            blocks = []

            # Loop through each entry in the collection
            for entry in entries:
                
                # Extract necessary fields for Block initialization
                index = entry.get("index")
                previous_hash = entry.get("previous_hash")
                ttransactions = entry.get("transactions")
                transactions = []
                for tx in ttransactions:
                    transactions.append(tx_from_json(tx))
                nonce = entry.get("nonce")
                
                # Initialize Block object
                block = Block(index=index, 
                              previous_hash=previous_hash, 
                              transactions=transactions, 
                              nonce=nonce)
                block.timestamp = entry.get("timestamp")
                block.merkle_root = entry.get("merkle_root")
                block.hash = entry.get("hash")
                
                # Append the Block object to the list
                blocks.append(block)
                
            self.chain = blocks
            print("Loaded blockchain from cloud database.")

        except:
            print(traceback.format_exc())
            self.chain = ep_load('blockchain', os.getenv("KEY"))
            print("Couldn't load blockchain from cloud, loaded from local file. ")

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

