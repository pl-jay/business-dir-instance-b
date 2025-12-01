from django.conf import settings
from django.db import models

class UserWallet(models.Model):
    """
    A non-custodial wallet linked to a user.
    Future-proof fields:
      - chain: which network family key from settings.CHAINS (default 'eth')
      - scheme: signing scheme (default 'eip191' / personal_sign)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallets",
    )
    address = models.CharField(max_length=42, db_index=True)
    chain = models.CharField(max_length=32, default="eth", db_index=True)
    scheme = models.CharField(max_length=32, default="eip191", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["address"], name="uniq_wallet_address_globally"),
            models.UniqueConstraint(fields=["user", "address"], name="uniq_user_address_pair"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.address}"
