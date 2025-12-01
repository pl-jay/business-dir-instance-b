from django.contrib import admin
from .models import OnChainRecord
from django.http import HttpResponse
import csv

@admin.register(OnChainRecord)
class OnChainRecordAdmin(admin.ModelAdmin):
    list_display = ("kind","business","review","chain","tx_hash","created_at")
    list_filter = ("kind","chain")
    actions = ["export_csv"]

    def export_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = "attachment; filename=onchain.csv"
        w = csv.writer(resp)
        w.writerow(["kind","business","review","chain","tx_hash","note","created_at"])
        for r in queryset:
            w.writerow([r.kind, r.business_id, r.review_id, r.chain, r.tx_hash, r.note, r.created_at.isoformat()])
        return resp
