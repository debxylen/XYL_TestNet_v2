from flask import Flask, request, jsonify
from blockchain import Blockchain
import os
import logging
import atexit
import traceback
from flask_cors import cross_origin
from errors import *
# Initialize Flask app and blockchain
app = Flask(__name__)
blockchain = Blockchain()

# Disable Flask default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
log.disabled = True

# Save blockchain and balances on exit
@atexit.register
def shutdown():
    blockchain.save_chain()
    blockchain.save_contracts()
    blockchain.save_balances()

CHAIN_ID = 6934  # Set your chain ID here


@app.route('/', methods=['GET', 'POST'])
def home():
    return "XYL TestNet is alive and working properly."


def handle_rpc(data):
    method = data.get('method')
    if method == 'eth_chainId':
        return jsonify({'jsonrpc': '2.0', 'result': hex(CHAIN_ID), 'id': data.get('id')})

    if method == 'eth_blockNumber':
        return jsonify({'jsonrpc': '2.0', 'result': hex(len(blockchain.chain) - 1), 'id': data.get('id')})

    if method == 'eth_getBlockByNumber':
        return handle_get_block_by_number(data)

    if method == 'eth_getBalance':
        return handle_get_balance(data)

    if method == 'eth_getTransactionByHash':
        return handle_get_transaction_by_hash(data)

    if method == 'eth_getBlockByHash':
        return handle_get_block_by_hash(data)

    if method == 'eth_getCode':
        return jsonify({'jsonrpc': '2.0', 'result': '0x', 'id': data.get('id')})

    if method == 'eth_estimateGas':
        return handle_estimate_gas(data)

    if method == 'eth_gasPrice':
        return jsonify({'jsonrpc': '2.0', 'result': hex(1), 'id': data.get('id')})

    if method == 'eth_getTransactionCount':
        return handle_get_transaction_count(data)

    if method == 'eth_sendRawTransaction':
        return handle_send_raw_transaction(data)

    if method == 'net_version':
        return jsonify({'jsonrpc': '2.0', 'result': "2", 'id': data.get('id')})

    if method == 'eth_getTransactionReceipt':
        return handle_get_transaction_receipt(data)

    return jsonify({'jsonrpc': '2.0', 'error': 'Method not found', 'id': data.get('id')})


def handle_get_block_by_number(data):
    block_number = int(data.get('params')[0], 16)
    if block_number >= len(blockchain.chain):
        return jsonify({'jsonrpc': '2.0', 'result': None, 'id': data.get('id')})
    return jsonify({'jsonrpc': '2.0', 'result': blockchain.chain[block_number].__json__(), 'id': data.get('id')})


def handle_get_balance(data):
    address = str(data.get('params')[0])
    balance = blockchain.get_balance(address)
    return jsonify({'jsonrpc': '2.0', 'result': hex(balance), 'id': data.get('id')})


def handle_get_transaction_by_hash(data):
    tx_hash = data.get('params')[0]
    transaction = blockchain.get_transaction_by_hash(tx_hash)
    return jsonify({'jsonrpc': '2.0', 'result': transaction, 'id': data.get('id')})


def handle_get_block_by_hash(data):
    block_hash = data.get('params')[0]
    block = blockchain.get_block_by_hash(block_hash)
    return jsonify({'jsonrpc': '2.0', 'result': block.__json__(), 'id': data.get('id')})


def handle_estimate_gas(data):
    gasp = int(data['params'][0]['gasPrice'], 16)  # in wei
    amt = int(data['params'][0]['value'], 16)  # tx value is always sent in wei
    gasunits = int(amt * 0.003469)
    return jsonify({'jsonrpc': '2.0', 'result': hex(gasunits * gasp), 'id': data.get('id')})


def handle_get_transaction_count(data):
    address = data.get('params')[0]
    count = blockchain.get_transaction_count(address)
    return jsonify({'jsonrpc': '2.0', 'result': hex(count), 'id': data.get('id')})


def handle_send_raw_transaction(data):
    raw_transaction = data.get('params')[0]
    block_number = blockchain.send_raw_transaction(raw_transaction)
    if "contractAddress" in block_number:
        return jsonify({'jsonrpc': '2.0', 'result': block_number["contractAddress"], 'id': data.get('id')})
    if "data" in block_number:
        return jsonify({'jsonrpc': '2.0', 'result': block_number["data"], 'id': data.get('id')})
    if "blockNumber" in block_number:
        return jsonify({'jsonrpc': '2.0', 'result': block_number["blockNumber"], 'id': data.get('id')})
    if "result" in block_number:
        return jsonify({'jsonrpc': '2.0', 'result': block_number["result"], 'id': data.get('id')})
    if "result" in block_number:
        return jsonify({'jsonrpc': '2.0', 'result': block_number["error"], 'id': data.get('id')})
    else:
        return jsonify({'jsonrpc': '2.0', 'error': {'code': -32603, 'message': 'Internal error'}, 'id': data.get('id')})


def handle_get_transaction_receipt(data):
    transaction_hash = data['params'][0]
    receipt = blockchain.get_transaction_receipt(str(transaction_hash))
    return jsonify({'jsonrpc': '2.0', 'result': receipt, 'id': data.get('id')})


@app.route('/rpc/', methods=['POST'])
@cross_origin()
def rpc():
    data = request.get_json()
    try:
        return handle_rpc(data)
    except Exception as e:
        return jsonify({'jsonrpc': '2.0', 'error': str(e), 'id': data.get('id')})


@app.route('/admin/add_balance', methods=['POST'])
def add_money():
    data = request.get_json()
    sender = data.get('sender')
    recipient = data.get('recipient')
    amount = data.get('amount')
    auth = data.get('auth')

    if auth != os.environ.get('ADMIN_AUTH'):
        return jsonify({"message": "Unauthorized", "status": "error"}), 400

    if not sender or not recipient or not amount:
        return jsonify({"message": "Invalid input. Sender, recipient, and amount are required.", "status": "error"}), 400

    result = blockchain.add_transaction(sender, recipient, amount)
    return jsonify({"message": "Transaction recorded and waiting to be mined.", "status": "success"}), 200


@app.route('/get_mining_job', methods=['GET'])
@cross_origin()
def get_mining_job():
    """Send a new mining job to the miner."""
    job = blockchain.generate_mining_job()
    return jsonify(job)


@app.route('/submit_mined_block', methods=['POST'])
@cross_origin()
def submit_mined_block():
    """Receive a mined block from a miner and validate it."""
    data = request.json
    miner_address = data.get('miner')
    miner_nonce = data.get('nonce')
    block_data = data.get('block_data')

    mined_block = {
        'index': block_data['index'],
        'hash': block_data['hash'],
        'previous_hash': block_data['previous_hash'],
        'transactions': block_data['transactions'],
        'nonce': miner_nonce,
        'difficulty': block_data['difficulty']
    }

    result = blockchain.submit_mined_block(mined_block, miner_address)
    if result:
        return jsonify({'message': 'Block accepted.'}), 200
    else:
        return jsonify({'message': 'Block rejected.'}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
