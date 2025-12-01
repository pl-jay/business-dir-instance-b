import binascii, re
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from eth_account import Account
from eth_account.messages import encode_defunct, defunct_hash_message

from apps.reviews.models import Review, ReviewSignature
from apps.onchain.models import OnChainRecord

ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")

def _review_digest_text(review: Review, user) -> str:
    """
    Canonical text the wallet signs. Keep this stable.
    """
    ts = int(review.created_at.timestamp()) if hasattr(review, "created_at") else 0
    lines = [
        "Sign review on Patriot Directory",
        f"Review:{review.id}",
        f"User:{user.id}",
        f"Business:{review.business_id}",
        f"Created:{ts}",
    ]
    return "\n".join(lines)

def _recover_address_from_signature(message_text: str, signature_hex: str) -> str | None:
    """
    Robust recovery: try text, hex-of-text, and pre-hash variants.
    """
    norm = (message_text or "").replace("\r\n", "\n")
    # A) plain text
    try:
        msg = encode_defunct(text=norm)
        return Account.recover_message(msg, signature=signature_hex)
    except Exception:
        pass
    # B) hex-of-text
    try:
        b = norm.encode("utf-8")
        hexmsg = "0x" + binascii.hexlify(b).decode()
        msg = encode_defunct(hexstr=hexmsg)
        return Account.recover_message(msg, signature=signature_hex)
    except Exception:
        pass
    # C) hash-of-text
    try:
        h = defunct_hash_message(text=norm)
        return Account.recoverHash(h, signature=signature_hex)
    except Exception:
        return None

@login_required
@require_GET
def review_digest(request, pk: int):
    """
    Return the canonical digest string for the current user to sign for this review.
    Only the author can request a digest for their review.
    """
    try:
        r = Review.objects.select_related("user", "business").get(pk=pk)
    except Review.DoesNotExist:
        return HttpResponseBadRequest("review not found")

    if r.user_id != request.user.id:
        return HttpResponseForbidden("not your review")

    digest = _review_digest_text(r, request.user)
    return JsonResponse({"digest": digest})

@login_required
@require_POST
def review_sign(request, pk: int):
    """
    Accepts address + signature for the canonical digest and stores a ReviewSignature.
    Also writes an OnChainRecord(kind='SIGNED_REVIEW') for the activity feed.
    """
    try:
        r = Review.objects.select_related("business").get(pk=pk)
    except Review.DoesNotExist:
        return HttpResponseBadRequest("review not found")

    if r.user_id != request.user.id:
        return HttpResponseForbidden("not your review")

    address = (request.POST.get("address") or "").strip()
    signature = (request.POST.get("signature") or "").strip()
    if not ADDR_RE.match(address) or not signature:
        return HttpResponseBadRequest("invalid payload")

    # Rebuild the exact digest we gave in GET /digest/
    digest = _review_digest_text(r, request.user)

    # Recover signer and compare
    recovered = _recover_address_from_signature(digest, signature)
    if not recovered or recovered.lower() != address.lower():
        return HttpResponseBadRequest("bad signature")

    # Compute a stable message hash to store (Keccak of EIP-191 defunct hash)
    # Using defunct_hash_message keeps it consistent with personal_sign semantics.
    msg_hash = defunct_hash_message(text=digest).hex()

    # Idempotent create (one signature per review)
    sig, created = ReviewSignature.objects.get_or_create(
        review=r,
        defaults={
            "signer_address": address,
            "message_hash": msg_hash,
            "signature": signature,
            "created_at": timezone.now(),
        },
    )

    # On-chain activity log (optional but per your MVP)
    OnChainRecord.objects.get_or_create(
        kind="SIGNED_REVIEW",
        review=r,
        defaults={"business": r.business, "created_at": timezone.now()},
    )

    return JsonResponse({"ok": True, "signed": True, "review_id": r.id, "address": address})
