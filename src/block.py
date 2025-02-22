import hashlib
import time
import json
import traceback
from errors import *
class Block:
    def __init__(self, index, previous_hash, transactions, nonce=0):
        """
        Initializes a new block.
        
        :param index: Position of the block in the blockchain.
        :param previous_hash: Hash of the previous block.
        :param transactions: List of transactions included in the block.
        :param nonce: Nonce used for Proof of Work (default is 0).
        """
        self.index = int(index)
        self.previous_hash = previous_hash
        self.timestamp = time.time()  # Current timestamp in seconds
        self.transactions = transactions  # List of transaction objects
        self.nonce = int(nonce)  # Used for Proof of Work
        self.merkle_root = self.compute_merkle_root()  # Root hash of transactions
        self.hash = self.compute_hash()  # Block hash

    def compute_hash(self):
        """
        Computes the SHA-256 hash of the block's contents.

        :return: A SHA-256 hash string of the block.
        """
        block_data = json.dumps({
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()

    def compute_merkle_root(self):
        """
        Computes the Merkle root for the transactions in the block.

        :return: Merkle root hash string or None if no transactions exist.
        """
        if not self.transactions:
            return None

        # Hash each transaction
        transaction_hashes = [
            hashlib.sha256(json.dumps(tx.__json__()).encode()).hexdigest() 
            for tx in self.transactions
        ]

        # Pair and hash recursively until one hash (Merkle root) remains
        while len(transaction_hashes) > 1:
            if len(transaction_hashes) % 2 != 0:  # Duplicate last hash if odd
                transaction_hashes.append(transaction_hashes[-1])

            transaction_hashes = [
                hashlib.sha256((transaction_hashes[i] + transaction_hashes[i + 1]).encode()).hexdigest()
                for i in range(0, len(transaction_hashes), 2)
            ]

        return transaction_hashes[0]

    def __json__(self):
        """
        Converts the block into a JSON-compatible dictionary.

        :return: Dictionary representation of the block.
        """
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'transactions': [tx.__json__() for tx in self.transactions],
            'nonce': self.nonce,
            'merkle_root': self.merkle_root,
            'hash': self.hash,
            'timestamp': self.timestamp
        }
