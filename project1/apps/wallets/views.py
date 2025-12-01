import secrets, time, re
import binascii
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from .models import UserWallet
from .services import verify_signature
from eth_account import Account
from eth_account.messages import encode_defunct, defunct_hash_message


ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
NONCE_TTL = 300  # 5 minutes

def _nonce_key(user_id): return f"wallets:nonce:{user_id}"

@login_required
@require_GET
def challenge(request):
    """
    Returns a one-time message to sign (nonce-bound).
    """
    nonce = secrets.token_hex(16)
    cache.set(_nonce_key(request.user.id), nonce, NONCE_TTL)
    msg = (
        "Sign in to Patriot Directory\n"
        f"User:{request.user.id}\n"
        f"Nonce:{nonce}\n"
        f"Ts:{int(time.time())}"
    )
    return JsonResponse({"message": msg})

def _to_hex(s: str) -> str:
    b = s.encode("utf-8")
    return "0x" + binascii.hexlify(b).decode()

@login_required
@require_POST
def verify(request):
    address = (request.POST.get("address") or "").strip()
    signature = (request.POST.get("signature") or "").strip()
    message = request.POST.get("message") or ""
    chain = (request.POST.get("chain") or "eth").strip()
    scheme = (request.POST.get("scheme") or "eip191").strip()

    if not ADDR_RE.match(address) or not signature or not message:
        return HttpResponseBadRequest("invalid payload")

    # 1) Nonce check
    expected = cache.get(_nonce_key(request.user.id))
    if not expected or f"Nonce:{expected}" not in message:
        return HttpResponseBadRequest("nonce expired")

    # 2) Normalize text (Windows CRLF -> LF)
    norm = message.replace("\r\n", "\n")
    ok = False
    recovered = None
    errors = []

    # Path A: verify as plain text (most wallets)
    try:
        msg = encode_defunct(text=norm)
        rec = Account.recover_message(msg, signature=signature)
        if rec.lower() == address.lower():
            ok, recovered = True, rec
        else:
            errors.append(("text", rec))
    except Exception as e:
        errors.append(("text_exc", repr(e)))

    # Path B: verify as hex of the text (some bridges)
    if not ok:
        try:
            hexmsg = _to_hex(norm)
            msg = encode_defunct(hexstr=hexmsg)
            rec = Account.recover_message(msg, signature=signature)
            if rec.lower() == address.lower():
                ok, recovered = True, rec
            else:
                errors.append(("hexstr", rec))
        except Exception as e:
            errors.append(("hexstr_exc", repr(e)))

    # Path C: verify via pre-hash of text (defunct_hash_message)
    if not ok:
        try:
            h = defunct_hash_message(text=norm)
            rec = Account.recoverHash(h, signature=signature)
            if rec.lower() == address.lower():
                ok, recovered = True, rec
            else:
                errors.append(("hash_text", rec))
        except Exception as e:
            errors.append(("hash_text_exc", repr(e)))

    if settings.DEBUG:
        print("wallet_verify DEBUG:",
              {"posted_address": address, "recovered": recovered, "ok": ok, "tried": errors})

    if not ok:
        return HttpResponseBadRequest("bad signature")

    # 3) Persist
    from .models import UserWallet
    UserWallet.objects.get_or_create(
        user=request.user,
        address=address,
        defaults={"chain": chain, "scheme": scheme},
    )

    cache.delete(_nonce_key(request.user.id))  # consume nonce

    return JsonResponse({"ok": True, "address": address, "chain": chain, "scheme": scheme})

@login_required
def wallet_status(request):
    linked = UserWallet.objects.filter(user=request.user).exists()
    return JsonResponse({"linked": linked})