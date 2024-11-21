from web3 import Web3
from eth_account import Account
from eth_account._utils.legacy_transactions import (
    serializable_unsigned_transaction_from_dict,
    encode_transaction,
)
import traceback

def recover_address_from_signed_tx(tx_):
    """Recover the sender address from a signed transaction."""
    # Extract relevant transaction fields
    tx = {k: v for k, v in tx_.items() if k in ['gasPrice', 'to', 'nonce', 'gas', 'value', 'data', 'r', 's', 'v']}
    
    # Ensure 'to' is a checksum address, but only if 'to' is not None
    if 'to' in tx and tx['to'] is not None and not Web3.is_checksum_address(tx['to']):
        tx['to'] = Web3.to_checksum_address(tx['to'])
    
    # Extract signature components
    v = int(tx['v'], 16) if isinstance(tx['v'], str) else tx['v']
    r = int(tx['r'], 16) if isinstance(tx['r'], str) else tx['r']
    s = int(tx['s'], 16) if isinstance(tx['s'], str) else tx['s']
    
    # Create unsigned transaction
    tx_details = {key: tx[key] for key in tx if key not in ['v', 'r', 's']}
    unsigned_tx = serializable_unsigned_transaction_from_dict(tx_details)
    
    # Encode and recover address
    signed_tx = encode_transaction(unsigned_tx, (v, r, s))
    recovered_address = Account.recover_transaction(signed_tx)
    
    return recovered_address

def verify_sign(tx):
    """Verify if the sender address matches the recovered address."""
    recovered_address = recover_address_from_signed_tx(tx)
    expected_address = tx.get('from') or tx.get('from_')
    return expected_address == recovered_address, recovered_address
