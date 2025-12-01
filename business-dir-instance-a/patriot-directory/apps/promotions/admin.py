from django.contrib import admin
from .models import Promotion, PromoClaim, TokenGate

@admin.register(TokenGate)
class TokenGateAdmin(admin.ModelAdmin):
    list_display = ("contract_address", "kind", "chain_id", "min_balance_wei", "required_token_id")
    search_fields = ("contract_address", "chain_id")

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "is_active", "starts_at", "ends_at", "max_claims", "total_claimed")
    list_filter = ("is_active", "business")
    search_fields = ("title", "business__name")

@admin.register(PromoClaim)
class PromoClaimAdmin(admin.ModelAdmin):
    list_display = ("promotion", "wallet_address", "code", "created_at")
    search_fields = ("wallet_address", "promotion__title")
