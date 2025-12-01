"""
Views for the reviews app.

Provides list, detail, create and update views for reviews. Creating and
editing reviews requires authentication; the current user is automatically
assigned as the review author.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView, FormView
from django.core.exceptions import PermissionDenied
from apps.directory.models import Business

from .models import OwnerReply, Review, ReviewAttachment, ReviewVote, ReviewReport
from .forms import ReviewForm, ReviewUpdateForm, ReviewReportForm
from django.db.models import Exists, OuterRef, Count, Q
from django.views.generic import ListView
# Note: Review is imported from .models above; avoid re-importing here to
# prevent shadowing.  ReviewAttachment, ReviewVote and ReviewReport are
# imported via the models import above.
from apps.wallets.models import UserWallet
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

class ReviewListView(ListView):
    """Display a list of reviews."""
    model = Review
    template_name = "reviews/review_list.html"
    context_object_name = "reviews"
    paginate_by = 20  # optional

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("user", "business")
            .prefetch_related("signature")  # 1:1 ReviewSignature
            .prefetch_related("attachments", "votes")
            .annotate(
                author_has_wallet=Exists(UserWallet.objects.filter(user_id=OuterRef("user_id"))),
                helpful_count=Count("votes", filter=Q(votes__is_helpful=True)),
                not_helpful_count=Count("votes", filter=Q(votes__is_helpful=False)),
            )
            .order_by("-created_at")
        )
        # Hide moderated/soft‑deleted reviews
        if hasattr(Review, "is_hidden"):
            qs = qs.filter(is_hidden=False)
        # Filter by business via ?business_id=<id>
        biz_id = self.request.GET.get("business_id")
        if biz_id:
            qs = qs.filter(business_id=biz_id)
        return qs

class ReviewDetailView(DetailView):
    model = Review
    template_name = "reviews/review_detail.html"
    context_object_name = "review"

    def get_queryset(self):
        # So the detail page also has the counts available without extra queries
        return (super().get_queryset().select_related("user", "business").prefetch_related("attachments")).annotate(helpful_count=Count("votes", filter=Q(votes__is_helpful=True)),not_helpful_count=Count("votes", filter=Q(votes__is_helpful=False)),)

class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_authenticated and obj.user_id == self.request.user.id

    def handle_no_permission(self):
        # You can either 403 or redirect; default is 403 when authenticated.
        return super().handle_no_permission()

class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm  # include custom fields and attachments
    template_name = "reviews/review_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.business = get_object_or_404(Business, slug=self.kwargs["business_slug"])
        # store the business based on slug in the URL

        owner_id = getattr(self.business, "owner_id", None) or getattr(self.business, "created_by_id", None)
        if request.user.is_authenticated and owner_id and owner_id == request.user.id:
            messages.info(request, "Owners cannot review their own business.")
            raise PermissionDenied("Owners cannot review their own business.")

        if Review.objects.filter(business=self.business, user=self.request.user).exists():
            messages.info(self.request, "You've already reviewed this business.")
            return redirect(self.business.get_absolute_url())

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.business = get_object_or_404(Business, slug=self.kwargs["business_slug"])
        # Ensure it's visible unless you intentionally moderate before showing
        if form.instance.is_hidden is None:
            form.instance.is_hidden = False
        response = super().form_valid(form)

        # Save attachments if you have multi-file upload
        for f in self.request.FILES.getlist("attachments"):
            ReviewAttachment.objects.create(review=self.object, file=f)

        return response

    def dispatch(self, request, *args, **kwargs):
        self.business = get_object_or_404(Business, slug=self.kwargs["business_slug"])
        if request.user.is_authenticated:
            already = Review.objects.filter(
                business=self.business, user=request.user, is_hidden=False
            ).exists()
            if already:
                messages.info(request, "You’ve already reviewed this business.")
                return redirect(self.business.get_absolute_url() + "#reviews")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        """Determine where to redirect after successfully submitting a review.

        Prefer an explicit ``next`` parameter passed in the query string or POST
        data.  If not provided, fall back to the HTTP_REFERER header (the page
        the user came from) and finally to the business detail page.  This
        method ensures that users creating a review are returned to the
        appropriate context rather than a now‑removed global review list.
        """
        # ``next`` may be supplied via GET or POST, e.g. /reviews/new/slug/?next=/some/page/
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        # HTTP_REFERER is sent by the browser and may not always be present
        referrer = self.request.META.get("HTTP_REFERER")
        # Default to the business detail page
        fallback = self.object.business.get_absolute_url()
        return next_url or referrer or fallback

    # def form_valid(self, form):
    #     # Associate the business and current user
    #     form.instance.business = self.business
    #     form.instance.user = self.request.user
    #     response = super().form_valid(form)
    #     # After saving the review instance, persist any uploaded attachments
    #     files = self.request.FILES.getlist("attachments")
    #     for f in files:
    #         ReviewAttachment.objects.create(review=self.object, file=f)
    #     return response

    # def get_success_url(self):
    #     return reverse("directory:detail", kwargs={"slug": self.object.business.slug})


class ReviewUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewUpdateForm

    def form_valid(self, form):
        response = super().form_valid(form)
        # Handle new attachments added during editing
        files = self.request.FILES.getlist("attachments")
        for f in files:
            ReviewAttachment.objects.create(review=self.object, file=f)
        return response

    def get_success_url(self):
        return reverse("directory:detail", kwargs={"slug": self.object.business.slug})

class ReviewDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Review

    def get_success_url(self) -> str:
        """Return to the associated business page after deleting a review.

        The success_url attribute referencing the now‑removed review list has
        been dropped.  This method ensures that upon deletion the user is
        redirected back to the business detail page where the review originally
        resided.
        """
        return reverse("directory:detail", kwargs={"slug": self.object.business.slug})

    # Soft‑delete reviews instead of removing them from the database.  This
    # preserves relationships (e.g. signatures) and avoids broken
    # references in business statistics.
    def delete(self, request, *args, **kwargs):  # type: ignore[override]
        self.object = self.get_object()
        self.object.is_hidden = True
        self.object.save(update_fields=["is_hidden"])
        return redirect(self.get_success_url())


@login_required
@require_POST
def review_vote(request, review_id: int) -> JsonResponse:
    """Handle AJAX requests to mark a review as helpful or not helpful.

    Expects a POST parameter ``is_helpful`` set to ``"true"`` or
    ``"false"``.  Toggles the vote: clicking the same option twice
    removes the vote.  Returns a JSON object with updated helpful and
    unhelpful counts.
    """
    review = get_object_or_404(Review, pk=review_id, is_hidden=False)
    val = request.POST.get("is_helpful")
    if val not in {"true", "false"}:
        return HttpResponseBadRequest("invalid payload")
    desired = val == "true"
    try:
        vote = ReviewVote.objects.get(review=review, user=request.user)
        # If user clicks the same vote again, remove it
        if vote.is_helpful == desired:
            vote.delete()
        else:
            vote.is_helpful = desired
            vote.save(update_fields=["is_helpful"])
    except ReviewVote.DoesNotExist:
        ReviewVote.objects.create(review=review, user=request.user, is_helpful=desired)
    # Compute counts
    helpful_count = review.votes.filter(is_helpful=True).count()
    unhelpful_count = review.votes.filter(is_helpful=False).count()
    return JsonResponse({"helpful": helpful_count, "unhelpful": unhelpful_count})


class ReviewReportView(LoginRequiredMixin, FormView):
    """Allow users to flag a review for moderation.

    Presents a simple form asking for the reason and an optional
    comment.  Only authenticated users may report reviews.  Each user
    can file one report per review; submitting a second report will
    update the existing record.
    """

    form_class = ReviewReportForm
    template_name = "reviews/report_form.html"

    def dispatch(self, request, *args, **kwargs):  # type: ignore[override]
        self.review = get_object_or_404(Review, pk=kwargs.get("review_id"), is_hidden=False)
        # Prevent owners from reporting their own reviews
        if self.review.user_id == request.user.id:
            return redirect(self.review.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ReviewReport.objects.update_or_create(
            review=self.review,
            reporter=self.request.user,
            defaults={
                "reason": form.cleaned_data["reason"],
                "comment": form.cleaned_data.get("comment", ""),
            },
        )
        return redirect(self.review.get_absolute_url())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["review"] = self.review
        return ctx

class OwnerReplyPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        review = self.get_review()
        # Only the owner of the business can reply
        return review.business.owner_id == self.request.user.id

    def get_review(self):
        return self.review

class OwnerReplyCreateView(LoginRequiredMixin, OwnerReplyPermissionMixin, CreateView):
    model = OwnerReply
    fields = ["text"]

    def dispatch(self, request, *args, **kwargs):
        from .models import Review
        self.review = get_object_or_404(Review, pk=kwargs["review_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.review = self.review
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.review.business.get_absolute_url()

class OwnerReplyUpdateView(LoginRequiredMixin, OwnerReplyPermissionMixin, UpdateView):
    model = OwnerReply
    fields = ["text"]

    def get_success_url(self):
        return self.object.review.business.get_absolute_url()