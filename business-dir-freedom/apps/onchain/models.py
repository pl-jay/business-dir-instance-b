"""
Models for storing on‑chain information associated with businesses.
"""

from django.db import models
from django.urls import reverse

from apps.directory.models import Business


class OnChainRecord(models.Model):
    KIND_CHOICES = (
        ("SIGNED_REVIEW", "Signed Review"),
        ("TX_LINKED", "Tx Linked"),
    )
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, db_index=True)
    business = models.ForeignKey(
        "directory.Business",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="onchain_records",   # <-- add this
    )
    wallet_address = models.CharField(
        max_length=42,
        help_text="Ethereum or other blockchain wallet address (e.g. 0xabc...)."
    )
    network = models.CharField(max_length=50, blank=True, help_text="Blockchain network, e.g. Ethereum, Polygon, etc.")
    proof = models.TextField(blank=True, help_text="Optional proof or transaction data verifying this record.")
    review = models.ForeignKey("reviews.Review", null=True, blank=True, on_delete=models.SET_NULL)
    chain = models.CharField(max_length=16, blank=True, null=True)  # 'eth'|'polygon'|'bsc'
    tx_hash = models.CharField(max_length=80, blank=True, null=True, db_index=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.business.name} – {self.wallet_address}"

    def get_absolute_url(self) -> str:
        """Return the canonical URL for this record."""
        return reverse("onchain:detail", kwargs={"pk": self.pk})
