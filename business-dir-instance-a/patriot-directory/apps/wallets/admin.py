from django.contrib import admin
from .models import UserWallet

@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    list_display = ("user", "address", "chain", "scheme", "created_at")
    search_fields = ("address",)
    list_filter = ("chain", "scheme", "created_at")
