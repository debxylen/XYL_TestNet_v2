import hashlib
import json
import time
import traceback
from errors import *

class Transaction:
    def __init__(self, sender, recipient, amount, nonce, timestamp=None):
        """Initializes a transaction.

        :param sender: Wallet address of the sender.
        :param recipient: Wallet address of the recipient.
        :param amount: Amount of XYL tokens being transferred.
        :param nonce: A unique identifier for this transaction. Used to prevent double-spending and for transaction replacement.
        :param timestamp: Optional timestamp; if None, current time is used.
        """
        self.sender = sender
        self.recipient = recipient
        try:
          self.amount = int(float(amount))
        except:
          self.amount = float(amount)

        self.nonce = int(nonce)  # Unique nonce for the transaction
        self.timestamp = timestamp or time.time()  # Default to current time
        self.tx_hash = self.compute_hash()  # Unique transaction hash for integrity

    def compute_hash(self):
        """Computes the SHA-256 hash of the transaction details.
        
        :return: SHA-256 hash string representing the transaction.
        """
        tx_string = json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'nonce': self.nonce,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def is_valid(self, sender_balance):
        """Validates the transaction.
        
        Ensures the amount is positive or zero, and the sender has sufficient balance.
        
        :param sender_balance: The current balance of the sender.
        :return: True if the transaction is valid, False otherwise.
        """
        if self.amount > sender_balance or self.amount < 0:
            return False
        return True

    def __json__(self):
        """Converts the transaction into a JSON-compatible dictionary.
        
        :return: A dictionary representation of the transaction.
        """
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'timestamp': self.timestamp,
            'amount': self.amount,
            'nonce': self.nonce,
            'hash': self.tx_hash
        }

def tx_from_json(data):
    """Reconstructs a Transaction object from a JSON dictionary.
    
    :param data: A dictionary containing transaction details.
    :return: A Transaction object.
    """
    sender = data['sender']
    recipient = data['recipient']
    amount = data['amount']
    nonce = data.get('nonce') or 0
    timestamp = data['timestamp']

    # Recreate the transaction
    tx = Transaction(sender, recipient, amount, nonce, timestamp)
    tx.tx_hash = data['hash']  # Set the hash explicitly for consistency
    return tx
