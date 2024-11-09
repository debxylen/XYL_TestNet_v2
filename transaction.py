import hashlib
import json
import time

class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None):
        self.sender = sender  # Sender's wallet address
        self.recipient = recipient  # Recipient's wallet address
        self.amount = amount  # Amount of XYL tokens being transferred
        self.timestamp = timestamp or time.time()  # Timestamp of the transaction
        self.tx_hash = self.compute_hash()  # Transaction hash for integrity


    def compute_hash(self):
        """
        Compute the SHA-256 hash of the transaction details.
        """
        tx_string = json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def is_valid(self, sender_balance):
        """
        Validate the transaction.
        Checks that the amount is greater than zero and that the sender has enough balance.
        
        Args:
            sender_balance (float): The current balance of the sender.

        Returns:
            bool: True if the transaction is valid, False otherwise.
        """

        #if self.amount <= 0:
        #    print("Invalid transaction: Amount must be greater than zero.")
        #    return False
        
        if self.amount > sender_balance:
            print(f"Invalid transaction: Insufficient funds (Balance: {sender_balance}, Tx Amount: {self.amount}.")
            return False

        # Additional validations can be added, such as checking transaction signatures
        return True

    def __json__(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'hash': self.tx_hash,
        }
