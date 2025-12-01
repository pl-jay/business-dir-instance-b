from django.contrib import admin
from .models import Ranking

@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ("business", "score", "created_at")
    search_fields = ("business__name",)
    list_filter = ("created_at",)
