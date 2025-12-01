from django.contrib import admin, messages
from django.utils import timezone
from .models import Business
from django.core.mail import send_mail

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name",  "category", "phone", "website","status", "submitted_by", "submitted_at", "approved_by", "approved_at")
    list_filter = ("status", "submitted_at")
    search_fields = ("name", "category", "address", "phone", "website")
    actions = ["approve_listings", "reject_listings"]
    prepopulated_fields = {"slug": ("name",)}
    
    @admin.action(description="Approve selected listings")
    def approve_listings(self, request, queryset):
        updated = 0
        for obj in queryset:
            obj.status = Business.Status.APPROVED
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
            obj.rejection_reason = ""
            obj.save(update_fields=["status", "approved_by", "approved_at", "rejection_reason"])
            updated += 1
            if obj.submitted_by and obj.submitted_by.email:
                send_mail(
                    "Your listing was approved",
                    f"Good news! '{obj.name}' is now live.",
                    None,
                    [obj.submitted_by.email],
                    fail_silently=True,
                )
        self.message_user(request, f"Approved {updated} listing(s).", level=messages.SUCCESS)

    @admin.action(description="Reject selected listings")
    def reject_listings(self, request, queryset):
        updated = queryset.update(
            status=Business.Status.REJECTED,
            approved_by=None,
            approved_at=None,
        )
        for obj in queryset:
            if obj.submitted_by and obj.submitted_by.email:
                send_mail(
                    "Your listing was rejected",
                    f"Unfortunately, your listing '{obj.name}' was not approved.",
                    None,
                    [obj.submitted_by.email],
                    fail_silently=True,
                )
        self.message_user(request, f"Rejected {updated} listing(s).", level=messages.WARNING)
