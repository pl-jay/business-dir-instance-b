from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import mail_admins
from .models import Business

@receiver(post_save, sender=Business)
def notify_admins_on_submission(sender, instance, created, **kwargs):
    if created and instance.status == Business.Status.PENDING:
        mail_admins(
            subject="New business submission pending review",
            message=f"{instance.name} submitted by {instance.submitted_by} needs moderation.",
            fail_silently=True,
        )
