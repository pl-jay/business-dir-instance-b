"""
Views for the onchain app.

Provides list, detail, create and update views for on‑chain records.
"""

import re
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from .models import OnChainRecord
from apps.directory.models import Business
from apps.reviews.models import ReviewSignature

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from .models import OnChainRecord


TX_RE = re.compile(r"^0x[a-fA-F0-9]{64}$")

@login_required
def onchain_index(request):
    rows = OnChainRecord.objects.select_related("business","review").all()[:200]
    # expand explorer
    explorers = getattr(settings, "ONCHAIN_EXPLORERS", {})
    return render(request, "onchain/index.html", {"rows": rows, "explorers": explorers})

@login_required
def link_tx(request, slug):
    biz = get_object_or_404(Business, slug=slug, owner=request.user)
    if request.method == "POST":
        chain = request.POST.get("chain")
        tx = request.POST.get("tx_hash","")
        note = request.POST.get("note","")
        if chain not in ("eth","polygon","bsc") or not TX_RE.match(tx):
            messages.error(request, "Invalid chain or tx hash")
        else:
            OnChainRecord.objects.create(kind="TX_LINKED", business=biz, chain=chain, tx_hash=tx, note=note)
            messages.success(request, "Transaction linked.")
        return redirect(biz.get_absolute_url())
    return render(request, "onchain/link_tx.html", {"business": biz})

# Hook: whenever a ReviewSignature is created, mirror into OnChainRecord
def mirror_signature_to_onchain(review_signature):
    OnChainRecord.objects.get_or_create(
        kind="SIGNED_REVIEW", review=review_signature.review,
        defaults={"business": review_signature.review.business}
    )


class OnChainListView(ListView):
    """Display a list of on‑chain records."""

    model = OnChainRecord
    template_name = "onchain/onchain_list.html"
    context_object_name = "records"


class OnChainDetailView(DetailView):
    """Display the details of a single on‑chain record."""

    model = OnChainRecord
    template_name = "onchain/onchain_detail.html"
    context_object_name = "record"


class OnChainCreateView(LoginRequiredMixin, CreateView):
    """Allow authenticated users to create new on‑chain records."""

    model = OnChainRecord
    fields = ["business", "wallet_address", "network", "proof"]
    template_name = "onchain/onchain_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_initial(self):
        initial = super().get_initial()
        w = self.request.user.wallets.first() if hasattr(self.request.user, "wallets") else None
        if w:
            initial["wallet_address"] = w.address
        return initial


class OnChainUpdateView(LoginRequiredMixin, UpdateView):
    """Allow authenticated users to edit existing on‑chain records."""

    model = OnChainRecord
    fields = ["business", "wallet_address", "network", "proof"]
    template_name = "onchain/onchain_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class OnChainDeleteView(LoginRequiredMixin, DeleteView):
    """Allow authenticated users to delete an on‑chain record."""

    model = OnChainRecord
    template_name = "onchain/onchain_confirm_delete.html"
    success_url = reverse_lazy("onchain:list")
