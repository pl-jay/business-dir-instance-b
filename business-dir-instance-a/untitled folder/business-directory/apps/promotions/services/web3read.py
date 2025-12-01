import os
from web3 import Web3
from functools import lru_cache

RPC_MAP = {
    "1":   os.getenv("ETH_RPC", "https://rpc.ankr.com/eth")
    }

ERC20_BALANCE_OF = Web3.keccak(text="balanceOf(address)")[:4].hex()  # 0x70a08231
ERC721_OWNER_OF   = Web3.keccak(text="ownerOf(uint256)")[:4].hex()   # 0x6352211e
ERC721_BALANCE_OF = ERC20_BALANCE_OF                                 # same sig

@lru_cache(maxsize=32)
def w3_for(chain_id: str) -> Web3:
    url = RPC_MAP.get(chain_id)
    if not url:
        raise ValueError(f"Unsupported chain_id {chain_id}")
    return Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 10}))

def pad32(hex_str: str) -> str:
    return hex_str.rjust(64, "0")

def addr_param(address: str) -> str:
    return "0" * 24 + address.lower().replace("0x", "")

def call_erc20_balance(chain_id: str, contract: str, address: str) -> int:
    w3 = w3_for(chain_id)
    data = ERC20_BALANCE_OF + addr_param(address)
    raw = w3.eth.call({"to": contract, "data": data})
    return int(raw.hex(), 16)

def erc721_owner_of(chain_id: str, contract: str, token_id: int) -> str:
    w3 = w3_for(chain_id)
    method = ERC721_OWNER_OF
    tid_hex = pad32(hex(token_id).replace("0x", ""))
    data = method + tid_hex
    raw = w3.eth.call({"to": contract, "data": data})
    owner_hex = "0x" + raw.hex()[-40:]
    return Web3.to_checksum_address(owner_hex)

def erc721_balance_of(chain_id: str, contract: str, address: str) -> int:
    return call_erc20_balance(chain_id, contract, address)
