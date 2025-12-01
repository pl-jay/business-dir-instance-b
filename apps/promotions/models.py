from django.conf import settings
from django.db import models
from django.utils import timezone

class TokenGate(models.Model):
    ERC20 = "erc20"
    ERC721 = "erc721"
    KIND_CHOICES = [(ERC20, "ERC-20"), (ERC721, "ERC-721")]

    chain_id = models.CharField(max_length=20, help_text="e.g., 1, 137, 56")
    contract_address = models.CharField(max_length=64, db_index=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=ERC20)
    min_balance_wei = models.DecimalField(max_digits=78, decimal_places=0, default=0)   # use wei for ERC20
    required_token_id = models.CharField(max_length=128, blank=True, default="")       # for ERC721 (optional)

    def __str__(self):
        return f"{self.get_kind_display()} @ {self.contract_address} (chain {self.chain_id})"


class Promotion(models.Model):
    # connect to your Directory Business model
    business = models.ForeignKey("directory.Business", on_delete=models.CASCADE, related_name="promotions")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # gate
    token_gate = models.ForeignKey(TokenGate, on_delete=models.PROTECT,related_name="promotions", null=True, blank=True)

    # fulfillment
    max_claims = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    total_claimed = models.PositiveIntegerField(default=0)

    # optional: unique code per claim
    generate_codes = models.BooleanField(default=False)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.business.name}: {self.title}"

    @property
    def is_open(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        if self.max_claims and self.total_claimed >= self.max_claims:
            return False
        return True


class PromoClaim(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name="claims")
    wallet_address = models.CharField(max_length=64, db_index=True)
    # store the message + signature to verify later if needed
    signed_message = models.TextField(blank=True, default="")
    signature = models.TextField(blank=True, default="")
    code = models.CharField(max_length=40, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("promotion", "wallet_address")  # prevent double-claim

    def __str__(self):
        return f"{self.wallet_address[:10]}… claimed {self.promotion_id}"
