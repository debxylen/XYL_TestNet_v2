import requests
import json

url = input("URL: ").strip()

# Test eth_sendTransaction
network_address = "Network"  # Replace with sender address
recipient_address = "0x2C0ce11bC9B0849781F7008db708E50EE1714Df7".lower()  # Replace with recipient address
response = requests.post(url, json={
    "jsonrpc": "2.0",
    "method": "eth_sendTransaction",
    "params": [{
        "from": network_address,
        "to": recipient_address,
        "value": str(hex(1 * 10**18))  # Amount in wei
    }],
    "id": 3
})
response = requests.post(url, json={"jsonrpc": "2.0", "method": "eth_getBalance", "params": [recipient_address, "latest"], "id": 1}) 
print("Recipient Balance:", response.json())
##
### get network balance
##response = requests.post(url, json={"jsonrpc": "2.0", "method": "eth_getBalance", "params": [network_address, "latest"], "id": 2})
##print("Network Balance:", response.json())
##
##response = requests.post(url, json={
##    "jsonrpc": "2.0",
##    "method": "eth_sendTransaction",
##    "params": [{
##        "from": network_address,
##        "to": recipient_address,
##        "value": str(hex(1 * 10**18))  # Amount in wei
##    }],
##    "id": 3
##})
##
##
##print(f"From {network_address} to {recipient_address}:", response.json())
##
##
##response = requests.post(url, json={"jsonrpc": "2.0", "method": "eth_getBalance", "params": [recipient_address, "latest"], "id": 4}) 
##print("Recipient Balance:", response.json())
##
##
##
