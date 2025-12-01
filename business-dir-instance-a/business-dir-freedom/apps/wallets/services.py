import re
from eth_account import Account
from eth_account.messages import encode_defunct

ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

class EvmPersonalSignVerifier:
    scheme = "eip191"

    @staticmethod
    def verify(address: str, message_text: str, signature: str) -> bool:
        if not ADDR_RE.match(address or ""):
            return False
        msg = encode_defunct(text=message_text)
        recovered = Account.recover_message(msg, signature=signature)
        return recovered.lower() == address.lower()

VERIFIERS = {
    "evm:eip191": EvmPersonalSignVerifier,
}

def verify_signature(family: str, scheme: str, address: str, message_text: str, signature: str) -> bool:
    key = f"{family}:{scheme}"
    cls = VERIFIERS.get(key)
    if not cls:
        return False
    return cls.verify(address, message_text, signature)
