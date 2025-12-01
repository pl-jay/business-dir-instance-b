from django.contrib import admin
from .models import (
    Review,
    ReviewSignature,
    ReviewAttachment,
    ReviewVote,
    ReviewReport,
)
from django.http import HttpResponse
import csv

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("id","business","user","rating","is_hidden","created_at")
    list_filter = ("is_hidden","created_at","rating")
    actions = ["hide_reviews", "export_reviews_csv"]

    def hide_reviews(self, request, queryset):
        queryset.update(is_hidden=True)
    hide_reviews.short_description = "Soft-hide selected reviews"

    def export_reviews_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = "attachment; filename=reviews.csv"
        w = csv.writer(resp)
        w.writerow(["id","business","user","rating","text","created_at","is_hidden"])
        for r in queryset:
            w.writerow([r.id, r.business_id, r.user_id, r.rating, r.text, r.created_at.isoformat(), r.is_hidden])
        return resp

@admin.register(ReviewSignature)
class ReviewSignatureAdmin(admin.ModelAdmin):
    list_display = ("review","signer_address","created_at")
    search_fields = ("signer_address",)

# Register additional models to make moderation easier in the admin interface.
@admin.register(ReviewAttachment)
class ReviewAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "file", "uploaded_at")
    search_fields = ("review__id",)


@admin.register(ReviewVote)
class ReviewVoteAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "user", "is_helpful", "created_at")
    list_filter = ("is_helpful",)
    search_fields = ("review__id", "user__username")


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "reporter", "reason", "created_at")
    list_filter = ("reason",)
    search_fields = ("review__id", "reporter__username")
