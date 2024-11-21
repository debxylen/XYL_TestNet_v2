from dataclasses import asdict, dataclass
from pprint import pprint
from typing import Optional
import traceback
import rlp
from eth_typing import HexStr
from eth_utils import keccak, to_bytes
from rlp.sedes import Binary, big_endian_int, binary
from web3 import Web3
from web3.auto import w3


class Transaction(rlp.Serializable):
    fields = [
        ("nonce", big_endian_int),
        ("gasPrice", big_endian_int),
        ("gas", big_endian_int),
        ("to", Binary.fixed_length(20, allow_empty=True)),
        ("value", big_endian_int),
        ("data", binary),
        ("v", big_endian_int),
        ("r", big_endian_int),
        ("s", big_endian_int),
    ]


@dataclass
class DecodedTx:
    hashTx: str
    from_: str
    to: Optional[str]
    nonce: int
    gas: int
    gasPrice: int
    value: int
    data: str
    chainId: int
    r: str
    s: str
    v: int


def hex_to_bytes(data: str) -> bytes:
    return to_bytes(hexstr=HexStr(data))


def decode_raw_tx(raw_tx: str):
    tx = rlp.decode(hex_to_bytes(raw_tx), Transaction)
    hashTx = Web3.to_hex(keccak(hex_to_bytes(raw_tx)))
    from_ = w3.eth.account.recover_transaction(raw_tx)
    to = w3.to_checksum_address(tx.to) if tx.to else None
    data = w3.to_hex(tx.data)
    r = hex(tx.r)
    s = hex(tx.s)
    chainId = (tx.v - 35) // 2 if tx.v % 2 else (tx.v - 36) // 2
    return DecodedTx(hashTx, from_, to, tx.nonce, tx.gas, tx.gasPrice, tx.value, data, chainId, r, s, str(hex(tx.v)))


def tx_decode(raw_tx):
    res = decode_raw_tx(raw_tx)
    return asdict(res)


