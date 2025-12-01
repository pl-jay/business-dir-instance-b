"""
Views for the business directory.

This module defines class-based views for listing businesses, showing details,
creating a new business, and updating an existing business. The create and
update views require authentication via ``LoginRequiredMixin``.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from django.core.paginator import Paginator          
from django.http import JsonResponse                 
from django.template.loader import render_to_string

from django.db.models.query import QuerySet
from django.core.cache import cache
from .models import Business
from django.db.models.functions import Lower
from apps.onchain.models import OnChainRecord
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Exists, Count, Avg, Q, BooleanField, Value, Case, When, CharField
from django.views.generic import DetailView, ListView
from apps.directory.models import Business
from apps.reviews.models import Review
from apps.wallets.models import UserWallet
from apps.reviews.models import ReviewVote
from .forms import BusinessForm

def business_list_api(request):
    qs = build_business_qs(request)
    paginator = Paginator(qs, 12)
    page = int(request.GET.get("page") or 1)
    page_obj = paginator.get_page(page)
    # Include badge sets for the card template; _cards_only.html includes
    # _business_card.html, which expects top_rated_ids and most_reviewed_ids.
    top_rated_ids, most_reviewed_ids = _top_sets()
    html = render_to_string(
        "directory/partials/_cards_only.html",
        {
            "items": page_obj.object_list,
            "top_rated_ids": top_rated_ids,
            "most_reviewed_ids": most_reviewed_ids,
        },
        request=request,
    )
    return JsonResponse(
        {
            "page": page_obj.number,
            "has_next": page_obj.has_next(),
            "html": html,
        }
    )

def build_business_qs(request) -> QuerySet:
    """
    Build a queryset for the business list based on query parameters.

    Supported parameters:
      - q: free‑text search across name, description, address and phone.
      - category: filter businesses by exact category (case‑insensitive).
      - location: filter by substring match on the address field.
      - sort: control ordering.  Supported values:
          • name (default): case‑insensitive alphabetical order.
          • -created_at: most recent first.
          • avg_rating or -avg_rating: order by average review rating.
          • reviews or -reviews: order by total number of reviews.

    The function adds the required annotations when sorting by rating or review
    count and always returns a distinct queryset.
    """
    qs: QuerySet = Business.objects.approved().order_by("-approved_at", "name")

    q = request.GET.get("q")
    category = request.GET.get("category")
    location = request.GET.get("location")
    sort = request.GET.get("sort") or "name"

    # Basic filtering
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(address__icontains=q) |
            Q(phone__icontains=q)
        )
    if category:
        qs = qs.filter(category__iexact=category)
    if location:
        # Simple substring match on address; more advanced geocoding could be added later.
        qs = qs.filter(address__icontains=location)

    # Sorting logic
    if sort in {"avg_rating", "-avg_rating", "reviews", "-reviews"}:
        # Annotate average rating and review count when needed.  Hidden reviews are excluded.
        qs = qs.annotate(
            review_count=Count(
                "reviews",
                filter=Q(reviews__is_hidden=False),
            ),
            avg_rating=Avg(
                "reviews__rating",
                filter=Q(reviews__is_hidden=False),
            ),
        )
        if sort == "avg_rating":
            qs = qs.order_by("avg_rating", "id")
        elif sort == "-avg_rating":
            qs = qs.order_by("-avg_rating", "id")
        elif sort == "reviews":
            qs = qs.order_by("review_count", "id")
        elif sort == "-reviews":
            qs = qs.order_by("-review_count", "id")
    else:
        # Stable ordering with a clear tiebreaker
        if sort == "name":
            qs = qs.order_by(Lower("name"), "id")          # case‑insensitive + id
        elif sort == "-created_at":
            qs = qs.order_by("-created_at", "id")         # newest + id
        else:
            qs = qs.order_by(Lower("name"), "id")         # default alphabetical + id

    # Belt & suspenders: if any future JOINs/annotations occur, avoid dup rows
    qs = qs.distinct()
    return qs

def get_context_data(self, **kwargs):
    ctx = super().get_context_data(**kwargs)
    b = self.object
    ctx["onchain_records"] = (
        OnChainRecord.objects
        .filter(business=b)
        .select_related("business", "review")
        .order_by("-created_at")
    )
    return ctx

from django.shortcuts import get_object_or_404, render

def business_detail(request, slug):
    biz = get_object_or_404(
        Business.objects.prefetch_related("reviews__user"),
        slug=slug
    )

    # Only visible reviews
    base_qs = (
        biz.reviews.filter(is_hidden=False)
        .select_related("user")
        .order_by("-created_at")
    )

    # Current user's vote subqueries (if authenticated)
    if request.user.is_authenticated:
        user_vote_sq = ReviewVote.objects.filter(
            review=OuterRef("pk"), user=request.user
        ).values("is_helpful")[:1]  # True / False
        user_voted_exists = ReviewVote.objects.filter(
            review=OuterRef("pk"), user=request.user
        )
    else:
        # Anonymous: no vote
        user_vote_sq = ReviewVote.objects.none().values("is_helpful")[:1]
        user_voted_exists = ReviewVote.objects.none()

    # Annotate counts and current user's vote status
    qs = (
        base_qs
        .annotate(
            helpful_count=Count("votes", filter=Q(votes__is_helpful=True), distinct=True),
            not_helpful_count=Count("votes", filter=Q(votes__is_helpful=False), distinct=True),
            _user_voted=Exists(user_voted_exists),
            _user_is_helpful=Subquery(user_vote_sq, output_field=BooleanField()),
        )
        .annotate(
            user_vote=Case(
                When(_user_voted=False, then=Value(None, output_field=CharField())),
                When(_user_is_helpful=True, then=Value("helpful", output_field=CharField())),
                When(_user_is_helpful=False, then=Value("not_helpful", output_field=CharField())),
                default=Value(None, output_field=CharField()),
                output_field=CharField(),
            )
        )
    )

    # Paginate the annotated queryset
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Business-level totals across visible reviews
    totals = base_qs.aggregate(
        total_helpful=Count("votes", filter=Q(votes__is_helpful=True), distinct=True),
        total_not_helpful=Count("votes", filter=Q(votes__is_helpful=False), distinct=True),
    )

    return render(
        request,
        "directory/business_detail.html",
        {
            "business": biz,
            "page_obj": page_obj,         # paginated reviews (each row has helpful_count/not_helpful_count/user_vote)
            "review_vote_totals": totals, # {"total_helpful": X, "total_not_helpful": Y}
        },
    )

def _top_sets():
    cache_key = "rankings:top_sets"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # --- your existing code ---
    top_rated_ids = list(
        Business.objects.annotate(
            review_count=Count("reviews", filter=Q(reviews__is_hidden=False)),
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_hidden=False)),
        )
        .filter(review_count__gte=3)
        .order_by("-avg_rating", "-review_count")
        .values_list("id", flat=True)[:10]
    )

    since = timezone.now() - timezone.timedelta(days=30)
    most_reviewed_ids = list(
        Business.objects.annotate(
            reviews_30d=Count(
                "reviews",
                filter=Q(reviews__is_hidden=False, reviews__created_at__gte=since),
            )
        )
        .filter(reviews_30d__gt=0)
        .order_by("-reviews_30d", "name")
        .values_list("id", flat=True)[:10]
    )

    result = (set(top_rated_ids), set(most_reviewed_ids))
    cache.set(cache_key, result, 300)  # 5 minutes
    return result

class BusinessDetailView(DetailView):
    model = Business
    template_name = "directory/business_detail.html"
    context_object_name = "b"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self, queryset=None):
        print("Getting business object...")
        obj = super().get_object(queryset)
        if obj.is_published:
            print("Business is published.")
            return obj
        # Allow owners and staff to see their own pending/rejected via direct link
        user = self.request.user
        print(user.is_staff)
        if user.is_authenticated and (user.is_staff or obj.submitted_by_id == user.id):
            return obj
        raise Http404("Business not found")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        b = self.object

        # Base reviews for this business
        base_reviews = (
            Review.objects.filter(business=b)
            .select_related("user")
            .prefetch_related("signature")
            .order_by("-created_at")
        )
        if hasattr(Review, "is_hidden"):
            base_reviews = base_reviews.filter(is_hidden=False)

        # Wallet chip
        base_reviews = base_reviews.annotate(
            author_has_wallet=Exists(
                UserWallet.objects.filter(user_id=OuterRef("user_id"))
            )
        )

        # User vote subqueries
        if self.request.user.is_authenticated:
            user_vote_sq = ReviewVote.objects.filter(
                review=OuterRef("pk"), user=self.request.user
            ).values("is_helpful")[:1]
            user_voted_exists = ReviewVote.objects.filter(
                review=OuterRef("pk"), user=self.request.user
            )
        else:
            user_vote_sq = ReviewVote.objects.none().values("is_helpful")[:1]
            user_voted_exists = ReviewVote.objects.none()

        # Add vote counts and current user's vote label
        reviews_qs = (
            base_reviews
            .annotate(
                helpful_count=Count("votes", filter=Q(votes__is_helpful=True), distinct=True),
                not_helpful_count=Count("votes", filter=Q(votes__is_helpful=False), distinct=True),
                _user_voted=Exists(user_voted_exists),
                _user_is_helpful=Subquery(user_vote_sq, output_field=BooleanField()),
            )
            .annotate(
                user_vote=Case(
                    When(_user_voted=False, then=Value(None, output_field=CharField())),
                    When(_user_is_helpful=True, then=Value("helpful", output_field=CharField())),
                    When(_user_is_helpful=False, then=Value("not_helpful", output_field=CharField())),
                    default=Value(None, output_field=CharField()),
                    output_field=CharField(),
                )
            )
        )

        # Business-level totals (visible reviews only)
        totals = base_reviews.aggregate(
            total_helpful=Count("votes", filter=Q(votes__is_helpful=True), distinct=True),
            total_not_helpful=Count("votes", filter=Q(votes__is_helpful=False), distinct=True),
        )

        ctx["reviews"] = reviews_qs
        ctx["is_owner"] = self.request.user.is_authenticated and b.owner_id == self.request.user.id
        ctx["top_rated_ids"], ctx["most_reviewed_ids"] = _top_sets()
        ctx["review_vote_totals"] = totals
        return ctx

class BusinessListView(ListView):
    """
    Display a paginated list of businesses with search and filter functionality.

    This view relies on ``build_business_qs`` to handle filtering and sorting.  It
    also provides additional context variables used by the template:

      - q: the current free‑text search term (string)
      - location: the current location filter (string)
      - selected_category: the currently selected category (string)
      - sort: the sorting parameter (string)
      - all_categories: a list of all distinct categories
      - top_categories: a list of dicts with keys ``category`` and ``count`` for the most frequent categories
      - top_rated_ids and most_reviewed_ids: sets of business IDs used for badge display

    The template expects the variable ``items`` to contain the list of businesses for
    the current page.  To match this, ``context_object_name`` is set to ``items``.
    """

    model = Business
    template_name = "directory/business_list.html"
    context_object_name = "items"
    paginate_by = 12

    def get_queryset(self) -> QuerySet:
        return build_business_qs(self.request)

    def get_context_data(self, **kwargs):
        from django.db.models import Count

        context = super().get_context_data(**kwargs)

        # search/filter parameters
        context["q"] = self.request.GET.get("q", "")
        context["location"] = self.request.GET.get("location", "")
        context["selected_category"] = self.request.GET.get("category", "")
        context["sort"] = self.request.GET.get("sort", "")

        # list of all categories (non‑empty)
        context["all_categories"] = (
            Business.objects.exclude(category="")
            .values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )

        # compute top categories by count
        top_categories = (
            Business.objects.exclude(category="")
            .values("category")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        context["top_categories"] = top_categories

        # top rated & most reviewed business IDs for badges
        top_rated_ids, most_reviewed_ids = _top_sets()
        context["top_rated_ids"] = top_rated_ids
        context["most_reviewed_ids"] = most_reviewed_ids

        return context

class BusinessCreateView(LoginRequiredMixin, CreateView):
    """Allow authenticated users to create a new business record."""

    model = Business
    form_class = BusinessForm
    template_name = "directory/business_form.html"
    success_url = reverse_lazy("directory:list")

    def form_valid(self, form):
        self.object = form.save(submitted_by=self.request.user)
        # Optionally flash a message here: “Submitted for review”
        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        uw = getattr(self.request.user, "wallets", None)
        if uw:
            first = uw.first()
            if first:
                initial["owner_wallet"] = first.address
        return initial

class BusinessUpdateView(LoginRequiredMixin, UpdateView):
    """Allow authenticated users to edit an existing business record."""

    model = Business
    fields = [
        "name",
        "category",
        "description",
        "address",
        "phone",
        "website",
    ]
    template_name = "directory/business_form.html"

    def get_success_url(self) -> str:
        """After saving, redirect back to the detail page."""
        return self.object.get_absolute_url()

    def get_initial(self):
        initial = super().get_initial()
        uw = self.request.user.wallets.first()
        if uw and not self.object.pk:  # only on create, or keep your own rule
            initial["owner_wallet"] = uw.address
        return initial

class BusinessDeleteView(LoginRequiredMixin, DeleteView):
    """Allow authenticated users to delete a business record."""

    model = Business
    template_name = "directory/business_confirm_delete.html"
    success_url = reverse_lazy("directory:list")

class MyBusinessListView(LoginRequiredMixin, ListView):
    """List of businesses submitted by the current user."""
    template_name = "directory/my_business_list.html"
    context_object_name = "businesses"
    paginate_by = 12

    def get_queryset(self):
        return (Business.objects
                .filter(submitted_by=self.request.user, is_deleted=False)
                .order_by("-submitted_at"))


from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator

@method_decorator(staff_member_required, name="dispatch")
class ModerationQueueView(ListView):
    template_name = "directory/moderation_queue.html"
    context_object_name = "businesses"
    paginate_by = 25

    def get_queryset(self):
        return (Business.objects
                .pending()
                .order_by("submitted_at"))
