from flask import Flask, request, jsonify
from blockchain import Blockchain
import json

app = Flask(__name__)
blockchain = Blockchain()

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True

import atexit
@atexit.register
def shutdown():
    blockchain.save_chain()
    blockchain.save_balances()

CHAIN_ID = 6934  # Set your chain ID here


@app.route('/', methods=['POST'])
def rpc():
    data = request.get_json()
    method = data.get('method')
    
    if method == 'eth_chainId':
        return jsonify({'jsonrpc': '2.0', 'result': hex(CHAIN_ID), 'id': data.get('id')})
    
    elif method == 'eth_blockNumber':
        #print("On block number: ", len(blockchain.chain) - 1)
        return jsonify({'jsonrpc': '2.0', 'result': hex(len(blockchain.chain) - 1), 'id': data.get('id')})
    
    elif method == 'eth_getBlockByNumber':
        block_number = int(data.get('params')[0], 16)
        if block_number >= len(blockchain.chain):
            return jsonify({'jsonrpc': '2.0', 'result': None, 'id': data.get('id')})
        return jsonify({'jsonrpc': '2.0', 'result': blockchain.chain[block_number].__json__(), 'id': data.get('id')})
    
    elif method == 'eth_sendTransaction':
        params = data.get('params')[0]
        sender = params['from']
        recipient = params['to']
        amount = int(params['value'],16)
        try:
            blockchain.add_transaction(sender, recipient, amount)
            return jsonify({'jsonrpc': '2.0', 'result': 'Transaction added', 'id': data.get('id')})
        except ValueError as e:
            return jsonify({'jsonrpc': '2.0', 'error': str(e), 'id': data.get('id')})

    elif method == 'eth_getBalance': 
        params = data.get('params')
        address = str(params[0])
        balance = blockchain.get_balance(address)
        print(f"{address} Balance {address in blockchain.balances}: {balance}")
        return jsonify({'jsonrpc': '2.0', 'result': hex(balance), 'id': data.get('id')})
    
    elif method == 'eth_getTransactionByHash':
        params = data.get('params')
        tx_hash = params[0]
        transaction = blockchain.get_transaction_by_hash(tx_hash)
        return jsonify({'jsonrpc': '2.0', 'result': transaction, 'id': data.get('id')})
    
    elif method == 'eth_getBlockByHash':
        params = data.get('params')
        block_hash = params[0]
        block = blockchain.get_block_by_hash(block_hash)
        return jsonify({'jsonrpc': '2.0', 'result': block.__json__(), 'id': data.get('id')})

    elif method == 'eth_getCode':
        return jsonify({
            'jsonrpc': '2.0',
            'result': '0x',
            'id': data.get('id')
        })

    elif method == 'eth_estimateGas':
        return jsonify({
            'jsonrpc': '2.0',
            'result': hex(50275),
            'id': data.get('id')
        })

    elif method == 'eth_gasPrice':
        return jsonify({
            'jsonrpc': '2.0',
            'result': hex(69_000_000_000), # 0.1gwei or 0.1449 rupees or 0.0021 XYL
            'id': data.get('id')
        })
    
    elif method == 'eth_getTransactionCount':
        address = data.get('params')[0]
        count = blockchain.get_transaction_count(address)
        return jsonify({
            'jsonrpc': '2.0',
            'result': hex(count),  
            'id': data.get('id')
        })

    elif method == 'eth_sendRawTransaction':
        raw_transaction = data.get('params')[0]
        block_number = blockchain.send_raw_transaction(raw_transaction)['blockNumber']
        
        if block_number is not None:
            return jsonify({
                'jsonrpc': '2.0',
                'result': block_number,
                'id': data.get('id')
            })
        else:
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32603, 'message': 'Internal error'},
                'id': data.get('id')
            })

    elif method == 'net_version':
        return jsonify({'jsonrpc': '2.0', 'result': "2", 'id': data.get('id')})

    elif method == 'eth_getTransactionReceipt':
        transaction_hash = data['params'][0]
        print(transaction_hash, data)
        try:
            receipt = blockchain.get_transaction_receipt(str(transaction_hash))
            print(receipt)
            return jsonify({'jsonrpc': '2.0', 'result': receipt, 'id': data.get('id')})
        except Exception as e:
            return jsonify({'jsonrpc': '2.0', 'error': str(e), 'id': data.get('id')})

    print(data)
    return jsonify({'jsonrpc': '2.0', 'error': 'Method not found', 'id': data.get('id')})

@app.route('/add_balance', methods=['POST','GET'])
def add_balance():
    data = request.get_json()
    address = data.get('address')
    amount = int(data.get('amount'))  # Assuming amount is provided in decimal

    # Here, you can add checks to ensure the address is valid
    if not address or amount <= 0:
        return jsonify({'jsonrpc': '2.0', 'error': 'Invalid address or amount', 'id': data.get('id')})

    # Create a transaction from your wallet address to the specified address
    sender_address = "Network"  # Replace with your wallet address
    try:
        blockchain.add_transaction(sender_address, address, amount)
        return jsonify({'jsonrpc': '2.0', 'result': 'Transaction added', 'id': data.get('id')})
    except ValueError as e:
        return jsonify({'jsonrpc': '2.0', 'error': str(e), 'id': data.get('id')})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8545)
