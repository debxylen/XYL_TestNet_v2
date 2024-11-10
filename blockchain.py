import hashlib
import json
from tx_decode import tx_decode
import time
from crypt_util import ep_save, ep_load
import os
import pickle
from block import Block
from transaction import Transaction
from dotenv import load_dotenv
import os
load_dotenv()

class Blockchain:
    def __init__(self):
        self.chain = []  # List of blocks (the chain)
        self.unconfirmed_transactions = []  # List of pending transactions
        self.balances = {}  # Dictionary to store balances
        self.u = (10**18)
        self.balances['network'] = 69420 * self.u
        self.create_genesis_block()
        if os.path.exists('blockchain'):
            self.load_chain()
        if os.path.exists('balances'):
            self.load_balances()
        print(self.balances)
            
    def create_genesis_block(self):
        """Generate the first block in the blockchain (the Genesis block)."""
        genesis_block = Block(0, "0", [], 0)
        genesis_block.hash = genesis_block.compute_hash()  # Compute the hash of the genesis block
        self.chain.append(genesis_block)  # Add it to the chain

    def add_transaction(self, sender, recipient, amount):
        """Add a new transaction to the list of unconfirmed transactions."""
        transaction = Transaction(sender, recipient, amount)
        if transaction.is_valid(sender_balance=self.get_balance(sender)):
            self.unconfirmed_transactions.append(transaction)  # Add to unconfirmed transactions
            self.update_balance(sender, -amount)  # Deduct amount from sender
            self.update_balance(recipient, amount)  # Add amount to recipient
            self.create_new_block()  # Create a new block immediately after adding transaction
            self.save_chain()
            self.save_balances()
        else:
            raise ValueError("Invalid transaction")

    def create_new_block(self):
        """Immediately add a block with all unconfirmed transactions."""
        last_block = self.get_last_block()
        new_block = Block(index=last_block.index + 1,
                          previous_hash=last_block.hash,
                          transactions=self.unconfirmed_transactions)
        
        # Add the new block to the chain
        new_block.hash = new_block.compute_hash()
        self.chain.append(new_block)
        
        # Clear unconfirmed transactions
        self.unconfirmed_transactions = []


    def get_last_block(self):
        """Retrieve the most recent block in the chain."""
        return self.chain[-1]

    def get_balance(self, address: str):
        """Retrieve the balance of the given address."""
        return self.balances.get(address.lower(), 0)  # Return 0 if address has no balance

    def get_transaction_by_hash(self, tx_hash):
        """Retrieve a transaction by its hash."""
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.hash == tx_hash:
                    return transaction
        return None

    def get_block_by_hash(self, block_hash):
        """Retrieve a block by its hash."""
        for block in self.chain:
            if str(block.hash) == str(block_hash):
                return block
        return None

    def update_balance(self, address, amount):
        """Update the balance for the given address."""
        address = address.lower()
        if address in self.balances:
            self.balances[address] += amount
        else:
            self.balances[address] = amount

    def send_raw_transaction(self, raw_transaction):
        try:
            tx_dict = tx_decode(raw_transaction)

            try:
                sender = tx_dict['from']
            except:
                sender = tx_dict['from_']
            try:
                recipient = tx_dict['to']
            except:
                recipient = tx_dict['to_']
                
            amount = tx_dict['value']  # value is in wei

            # Add the transaction to the blockchain
            self.add_transaction(sender, recipient, amount)

            return {
                'blockNumber': len(self.chain),  # Returning the current chain length as the "block number"
                'transactionHash': hashlib.sha256(raw_transaction.encode()).hexdigest()  # Example hash
            }
        except Exception as e:
            print(f"Error processing transaction: {e}")
            return None

    def add_money(self, recipient, amount):
        """Add a new transaction to the list of unconfirmed transactions."""
        sender = 'Network'
        transaction = Transaction(sender, recipient, amount)
        if transaction.is_valid(sender_balance=self.get_balance(sender)):
            self.unconfirmed_transactions.append(transaction)  # Add to unconfirmed transactions
            self.update_balance(sender, -amount)  # Deduct amount from sender
            self.update_balance(recipient, amount)  # Add amount to recipient
            self.create_new_block()  # Add block immediately
            self.save_chain()
            self.save_balances()
        else:
            raise ValueError("Invalid transaction")

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

    def get_transaction_receipt(self, transaction_id: str):
        """Get the transaction receipt for a specific transaction."""
        for block in self.chain:
            for index, transaction in enumerate(block.transactions):
                if int(block.index) == int(transaction_id)-1: 
                    return {
                        'blockHash': block.hash,
                        'blockNumber': hex(block.index),
                        'contractAddress': None,  
                        'cumulativeGasUsed': hex(50275), 
                        'effectiveGasPrice': hex(69_000_000_000),  # Set based on your logic
                        'from': transaction.sender,
                        'gasUsed': hex(50275),
                        'status': hex(1), 
                        'to': transaction.recipient,
                        'transactionHash': transaction.tx_hash,
                        'transactionIndex': hex(index),
                        'type': 0  # Adjust if needed based on transaction types
                    }
        raise ValueError("Transaction not found: ",transaction_id)

