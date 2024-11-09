import hashlib
import time
import json

class Block:
    def __init__(self, index, previous_hash, transactions, nonce=0):
        self.index = index  # Position of the block in the blockchain
        self.previous_hash = previous_hash  # Hash of the previous block
        self.timestamp = time.time()  # Creation timestamp
        self.transactions = transactions  # List of transactions
        self.nonce = nonce  # Nonce for Proof of Work
        self.merkle_root = self.compute_merkle_root()  # Merkle root of transactions
        self.hash = self.compute_hash()  # Hash of the block

    def compute_hash(self):
        """
        Compute a SHA-256 hash of the block's contents including the merkle root.
        """
        block_string = json.dumps({
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def compute_merkle_root(self):
        """
        Compute the Merkle root for the transactions in the block.
        The Merkle root is the hash of all transaction hashes, ensuring integrity.
        """
        if not self.transactions:
            return None
        
        # Hash each transaction
        transaction_hashes = [hashlib.sha256(json.dumps(tx.__json__()).encode()).hexdigest() for tx in self.transactions]
        
        # Compute the Merkle root by pairing up the transaction hashes and hashing them
        while len(transaction_hashes) > 1:
            if len(transaction_hashes) % 2 != 0:  # If odd, duplicate the last hash
                transaction_hashes.append(transaction_hashes[-1])
            temp_hashes = []
            for i in range(0, len(transaction_hashes), 2):
                combined_hash = hashlib.sha256((transaction_hashes[i] + transaction_hashes[i+1]).encode()).hexdigest()
                temp_hashes.append(combined_hash)
            transaction_hashes = temp_hashes
        
        return transaction_hashes[0]  # The root hash

    def __json__(self):
        return {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'transactions': [tx.__json__() for tx in self.transactions],
            'nonce': self.nonce,
            'merkle_root': self.merkle_root,
        }  
