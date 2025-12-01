from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.db import transaction
from web3 import Web3
from django.views.generic import ListView
from django.utils import timezone
from .models import Promotion, PromoClaim
from .services.web3read import call_erc20_balance, erc721_owner_of, erc721_balance_of

def promo_detail(request, pk: int):
    promo = get_object_or_404(Promotion, pk=pk, is_active=True)
    return render(request, "promotions/detail.html", {"promo": promo})

def _check_gate(promo: Promotion, wallet_address: str) -> dict:
    gate = promo.token_gate
    addr = Web3.to_checksum_address(wallet_address)
    if gate is None:
        return {"ok": False, "error": "Promo misconfigured (no token gate)."}
    if gate.kind == "erc20":
        bal = call_erc20_balance(gate.chain_id, Web3.to_checksum_address(gate.contract_address), addr)
        ok = bal >= int(gate.min_balance_wei)
        return {"ok": ok, "balance": str(bal)}
    else:
        # ERC-721
        if gate.required_token_id:
            owner = erc721_owner_of(gate.chain_id, Web3.to_checksum_address(gate.contract_address), int(gate.required_token_id))
            ok = (owner.lower() == addr.lower())
            return {"ok": ok, "owner": owner}
        else:
            bal = erc721_balance_of(gate.chain_id, Web3.to_checksum_address(gate.contract_address), addr)
            ok = bal > 0
            return {"ok": ok, "balance": str(bal)}

def promo_eligibility_api(request, pk: int):
    promo = get_object_or_404(Promotion, pk=pk, is_active=True)
    wallet = request.GET.get("wallet", "")
    if not wallet or not wallet.startswith("0x") or len(wallet) != 42:
        return JsonResponse({"ok": False, "error": "Invalid wallet"}, status=400)

    if not promo.is_open:
        return JsonResponse({"ok": False, "error": "Promo closed"}, status=400)

    # already claimed?
    if PromoClaim.objects.filter(promotion=promo, wallet_address__iexact=wallet).exists():
        return JsonResponse({"ok": False, "error": "Already claimed"}, status=400)

    res = _check_gate(promo, wallet)
    if not res.get("ok"):
        return JsonResponse(res, status=400)
    return JsonResponse(res, status=200 if res["ok"] else 403)

@require_POST
def promo_claim_api(request, pk: int):
    promo = get_object_or_404(Promotion, pk=pk, is_active=True)
    wallet = request.POST.get("wallet", "")
    message = request.POST.get("message", "")
    signature = request.POST.get("signature", "")

    if not promo.is_open:
        return JsonResponse({"ok": False, "error": "Promo closed"}, status=400)

    if not wallet or not wallet.startswith("0x") or len(wallet) != 42:
        return JsonResponse({"ok": False, "error": "Invalid wallet"}, status=400)

    # Basic replay/ownership check: verify signature recovers the wallet
    try:
        from eth_account.messages import encode_defunct
        from eth_account import Account
        msg = encode_defunct(text=message)
        recovered = Account.recover_message(msg, signature=signature)
        if recovered.lower() != wallet.lower():
            return JsonResponse({"ok": False, "error": "Signature mismatch"}, status=400)
    except Exception:
        return JsonResponse({"ok": False, "error": "Bad signature"}, status=400)

    # Gate re-check (avoid client tampering)
    res = _check_gate(promo, wallet)
    if not res["ok"]:
        return JsonResponse({"ok": False, "error": "Not eligible"}, status=403)

    # One per wallet
    if PromoClaim.objects.filter(promotion=promo, wallet_address__iexact=wallet).exists():
        return JsonResponse({"ok": False, "error": "Already claimed"}, status=400)

    with transaction.atomic():
        # capacity
        if promo.max_claims and promo.total_claimed >= promo.max_claims:
            return JsonResponse({"ok": False, "error": "Sold out"}, status=400)

        code = ""
        if promo.generate_codes:
            import secrets
            code = secrets.token_hex(8)

        PromoClaim.objects.create(
            promotion=promo,
            wallet_address=wallet,
            signed_message=message,
            signature=signature,
            code=code,
        )
        promo.total_claimed += 1
        promo.save(update_fields=["total_claimed"])

    return JsonResponse({"ok": True, "code": code})


class PromotionListView(ListView):
    model = Promotion
    template_name = "promotions/promotion_list.html"
    context_object_name = "promos"
    paginate_by = 12

    def get_queryset(self):
        now = timezone.now()
        qs = (Promotion.objects
              .select_related("business", "token_gate")
              .filter(is_active=True, token_gate__isnull=False))
        # only “open” promos (optional; match your is_open logic)
        qs = qs.filter(starts_at__lte=now).exclude(ends_at__lt=now)
        # sort newest first
        return qs.order_by("-starts_at", "-id")