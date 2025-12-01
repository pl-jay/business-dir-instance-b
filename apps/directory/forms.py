
from django import forms
from .models import Business

class BusinessForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = [
            "name",
            "category",
            "description",
            "address",
            "phone",
            "website",
            "slug",
        ]

    def save(self, submitted_by=None, commit=True):
        obj = super().save(commit=False)
        # Always reset to PENDING on create and when non-staff edits:
        if not obj.pk:
            obj.status = Business.Status.PENDING
        if submitted_by and not obj.submitted_by_id:
            obj.submitted_by = submitted_by
        if commit:
            obj.save()
        return obj
