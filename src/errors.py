# blockchain errors
class BlockchainError(Exception):
    """Base class for all blockchain-related errors."""
    pass

#transaction errors
class TransactionError(BlockchainError):
    """Base class for transaction-related errors."""
    pass

class InvalidTransactionError(TransactionError):
    """Raised when a transaction fails validation."""
    pass

class InsufficientBalanceError(TransactionError):
    """Raised when an account has insufficient funds for a transaction."""
    pass

class GasLimitExceededError(TransactionError):
    """Raised when the transaction exceeds the gas limit."""
    pass

class InvalidSignatureError(TransactionError):
    """Raised when a transaction's signature is invalid."""
    pass

class TransactionNotFoundError(TransactionError):
    """Raised when a requested transaction cannot be found."""
    pass

class RevertedTransactionError(TransactionError):
    """Raised when a transaction is reverted by the blockchain."""
    pass

#smartcontract errors
class SmartContractError(BlockchainError):
    """Base class for smart contract-related errors."""
    pass

class ContractNotFoundError(SmartContractError):
    """Raised when attempting to interact with a non-existent contract."""
    pass

class InvalidContractAddressError(SmartContractError):
    """Raised when an invalid contract address is provided."""
    pass

class MethodNotFoundError(SmartContractError):
    """Raised when a called method does not exist in the smart contract."""
    pass

class ExecutionError(SmartContractError):
    """Raised when a smart contract execution fails, can be due to errors in the contract code or during execution."""
    pass

class InvalidExecutionData(ExecutionError):
    """Raised when invalid data is passed during contract execution."""

class ContractLockedError(SmartContractError):
    """Raised when attempting to interact with a locked contract."""
    pass

class PermissionDeniedError(SmartContractError):
    """Raised when an unauthorized account attempts a restricted action."""
    pass

class InvalidCreationData(SmartContractError):
    """Raised when invalid data is passed during contract deployment."""
    pass

#blockchain state errors
class BlockchainStateError(BlockchainError):
    """Base class for blockchain state-related errors."""
    pass

class InvalidBlockError(BlockchainStateError):
    """Raised when a block fails validation."""
    pass

class ForkDetectedError(BlockchainStateError):
    """Raised when a blockchain fork is detected."""
    pass

class ConsensusError(BlockchainStateError):
    """Raised when consensus cannot be reached."""
    pass

class StateTransitionError(BlockchainStateError):
    """Raised when an invalid state transition is detected."""
    pass

#network errors
class NetworkError(BlockchainError):
    """Base class for network-related errors."""
    pass

class NodeConnectionError(NetworkError):
    """Raised when a node cannot connect to the network."""
    pass

class InvalidRPCRequestError(NetworkError):
    """Raised when an RPC request is malformed or invalid."""
    pass

class PeerNotFoundError(NetworkError):
    """Raised when a peer cannot be found on the network."""
    pass


