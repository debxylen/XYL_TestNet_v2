from web3 import Web3
import json
from eth_account import Account
from utils import *
from errors import *


class SmartContract:
    def __init__(self, owner, contractmngr, tdata=None):
        self.owner = owner.lower()
        self.state = {}
        self.manager = contractmngr
        self.locked = False
        self.native_methods = ["xyl_destroy", "xyl_transferOwner", "xyl_getInfo", "xyl_lock", "xyl_unlock"]
        
        # Generate contract address
        deployer_bytes = Web3.to_bytes(hexstr=owner)
        nonce_bytes = int(self.manager.blockchain.get_transaction_count(owner)).to_bytes(32, 'big')
        data = deployer_bytes + nonce_bytes
        self.address = Web3.keccak(data)[12:].hex()
        
        self.manager.add(self)
        if tdata:
            try:
                self.methods = json.loads(hex_to_string(tdata))
            except json.JSONDecodeError:
                raise InvalidCreationData("Failed to parse contract methods from transaction data.")
        else:
            self.methods = {}

    def balance(self) -> int:
        # Get the balance of the contract
        return int(self.manager.blockchain.get_balance(self.address))

    def send_funds(self, recipient, amount):
        # Send funds to the recipient
        if self.balance() < int(amount):
            raise InsufficientBalanceError("Insufficient contract balance.")
        self.manager.blockchain.add_transaction(self.address, recipient, int(amount))
        return 1

    def set(self, key, value):
        # Set a value in the contract state
        self.state[key] = value
        return 1

    def get(self, key):
        # Get a value from the contract state
        return self.state.get(key, None)

    def destroy(self, caller):
        # Destroy the contract if the caller is the owner
        caller = caller.lower()
        if caller != self.owner:
            raise PermissionDeniedError("Only the owner can destroy the contract.")
        self.manager.blockchain.add_transaction(self.address, self.owner, self.balance())  # send contract balance to owner
        self.manager.delete(self.address)
        return {"result": "Contract destroyed successfully"}

    def get_contract_info(self):
        return {
            "address": self.address,
            "owner": self.owner,
            "state": self.state,
            "locked": getattr(self, 'locked', False)  # Defaults to False if not locked
        }

    def transfer_ownership(self, new_owner, caller):
        # Ensure the caller is the current owner
        if caller.lower() != self.owner:
            raise PermissionDeniedError("Only the owner can transfer ownership.")
        # Update the owner to the new address
        self.owner = new_owner.lower()
        return {"result": "Ownership transferred successfully"}

    def lock(self, caller):
        if caller.lower() != self.owner:
            raise PermissionDeniedError("Only the owner can lock the contract.")
        self.locked = True
        return {"result": "Contract locked successfully"}

    def unlock(self, caller):
        if caller.lower() != self.owner:
            raise PermissionDeniedError("Only the owner can unlock the contract.")
        self.locked = False
        return {"result": "Contract unlocked successfully"}

    def emit_event(self, event_name, data):
        if not isinstance(event_name, str) or not isinstance(data, dict):
            raise InvalidExecutionData("Event name must be a string and data must be a dictionary.")
        event = {
            "event": event_name,
            "data": data,
            "timestamp": time.time()  # Current timestamp
        }
        self.manager.blockchain.event_log.append(event)
        return 1

    def execute(self, data, caller):
        caller = caller.lower()
        try:
            method_name, args = hex_to_string(data).split("|XYL|")
            args = json.loads(args)
        except (ValueError, json.JSONDecodeError) as e:
            raise InvalidExecutionData("Failed to parse execution data.") from e

        if self.locked and caller != self.owner:
            raise ContractLockedError("Contract is locked, and only the owner can execute methods.")

        if method_name in self.native_methods:
            if method_name == "xyl_destroy":
                return self.destroy(caller)
            elif method_name == "xyl_transferOwner":
                return self.transfer_ownership(args['newOwner'], caller)
            elif method_name == "xyl_getInfo":
                return self.get_contract_info()
            elif method_name == "xyl_lock":
                return self.lock(caller)
            elif method_name == "xyl_unlock":
                return self.unlock(caller)

        if method_name not in self.methods:
            raise MethodNotFoundError(f"Method '{method_name}' not found in contract.")

        instructions = self.methods[method_name]
        stack = []

        try:
            for instruction in instructions:
                parts = instruction.split(" ")
                op = parts[0]

                if op == "PUSH_ARG":
                    arg_name = parts[1]
                    if arg_name not in args:
                        raise InvalidExecutionData(f"Missing argument for {instruction}")
                    stack.append(args[arg_name])

                if op == "PUSH":
                    value = parts[1]
                    stack.append(value)

                elif op == "SET":
                    key = parts[1]
                    value = stack.pop()
                    result = self.set(key, value)
                    stack.append(result)

                elif op == "GET":
                    key = parts[1]
                    stack.append(self.get(key))

                elif op == "SEND_TX":
                    recipient_var = parts[1]
                    amount_var = parts[2]
                    recipient = self.get(recipient_var)
                    amount = self.get(amount_var)
                    if recipient is None or amount is None:
                        raise ExecutionError(f"Undefined variable(s) in SEND_TX: {recipient_var}, {amount_var}")
                    result = self.send_funds(recipient, amount)
                    stack.append(result)

                elif op == "GET_BALANCE":
                    stack.append(self.balance())

                elif op == "EMIT_EVENT":
                    event_name = self.get(parts[1])
                    data = self.get(parts[2])
                    if event_name is None or data is None:
                        raise ExecutionError(f"Event name '{event_name}' or data '{data}' is not defined.")
                    result = self.emit_event(event_name, data)
                    stack.append(result)

                elif op in ["ADD", "SUB", "MUL", "DIV", "MOD", "LT", "GT"]:
                    b = stack.pop()
                    a = stack.pop()
                    if op == "ADD":
                        stack.append(a + b)
                    elif op == "SUB":
                        stack.append(a - b)
                    elif op == "MUL":
                        stack.append(a * b)
                    elif op == "DIV":
                        if b == 0:
                            raise ZeroDivisionError("Division by zero")
                        stack.append(a / b)
                    elif op == "MOD":
                        if b == 0:
                            raise ZeroDivisionError("Division by zero in modulus operation")
                        stack.append(a % b)
                    elif op == "LT":
                        stack.append(1 if a < b else 0)
                    elif op == "GT":
                        stack.append(1 if a > b else 0)

                else:
                    raise ExecutionError(f"Unknown opcode: {op}")

            return {"result": "Execution successful", "state": self.state}
        except Exception as e:
            raise ExecutionError(f"Execution failed: {str(e)}") from e


class ContractManager:
    def __init__(self, blockchain):
        self.contracts = {}
        self.blockchain = blockchain

    def add(self, contract):
        self.contracts[contract.address] = contract

    def delete(self, c_address):
        if c_address not in self.contracts:
            raise ContractNotFoundError(f"Contract at address {c_address} does not exist.")
        del self.contracts[c_address]

    def exists(self, c_address):
        return c_address in self.contracts
