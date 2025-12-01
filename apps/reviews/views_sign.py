import hashlib, re
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from eth_account.messages import encode_defunct
from eth_account import Account
from .models import Review, ReviewSignature

ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
HEX_RE = re.compile(r"^0x[a-fA-F0-9]+$")

@login_required
@require_POST
def sign_review(request, pk):
    addr = request.POST.get("address", "")
    sig  = request.POST.get("signature", "")
    review = get_object_or_404(Review, pk=pk, is_hidden=False, user=request.user)

    # Create deterministic message hash client & server agree on:
    seed = f"{review.id}:{request.user.id}:{review.created_at.timestamp()}"
    digest = "0x" + hashlib.sha256(seed.encode()).hexdigest()

    if not ADDR_RE.match(addr) or not HEX_RE.match(digest) or not sig:
        return HttpResponseBadRequest("bad payload")

    msg = encode_defunct(text=digest)
    try:
        recovered = Account.recover_message(msg, signature=sig)
    except Exception:
        return HttpResponseBadRequest("bad signature")

    if recovered.lower() != addr.lower():
        return HttpResponseBadRequest("address mismatch")

    ReviewSignature.objects.update_or_create(
        review=review,
        defaults={"signer_address": addr, "message_hash": digest, "signature": sig},
    )
    return JsonResponse({"ok": True})
