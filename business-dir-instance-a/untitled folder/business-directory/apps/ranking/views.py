"""
Views for the ranking app.

Provides list, detail, create and update views for business rankings.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from .models import Ranking
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from apps.directory.models import Business
from apps.reviews.models import Review

@method_decorator(cache_page(60*5), name="dispatch")
class TopRated(ListView):
    model = Business
    template_name = "rankings/top_rated.html"
    context_object_name = "businesses"
    paginate_by = 20

    def get_queryset(self):
        return (Business.objects
            .annotate(
                review_count=Count("reviews", filter=Q(reviews__is_hidden=False)),
                avg_rating=Avg("reviews__rating", filter=Q(reviews__is_hidden=False)),
            )
            .filter(review_count__gte=3)
            .order_by("-avg_rating", "-review_count"))

@method_decorator(cache_page(60*5), name="dispatch")
class MostReviewed30d(ListView):
    model = Business
    template_name = "rankings/most_reviewed.html"
    context_object_name = "businesses"
    paginate_by = 20

    def get_queryset(self):
        since = timezone.now() - timezone.timedelta(days=30)
        return (Business.objects
            .annotate(
                reviews_30d=Count(
                    "reviews",
                    filter=Q(reviews__is_hidden=False, reviews__created_at__gte=since),
                )
            )
            .filter(reviews_30d__gt=0)
            .order_by("-reviews_30d", "name"))

class RankingListView(ListView):
    """Display a list of rankings."""

    model = Ranking
    template_name = "ranking/ranking_list.html"
    context_object_name = "rankings"


class RankingDetailView(DetailView):
    """Display a single ranking detail."""

    model = Ranking
    template_name = "ranking/ranking_detail.html"
    context_object_name = "ranking"


class RankingCreateView(LoginRequiredMixin, CreateView):
    """Allow authenticated users to create a ranking."""

    model = Ranking
    fields = ["business", "score", "comment"]
    template_name = "ranking/ranking_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class RankingUpdateView(LoginRequiredMixin, UpdateView):
    """Allow authenticated users to edit an existing ranking."""

    model = Ranking
    fields = ["business", "score", "comment"]
    template_name = "ranking/ranking_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class RankingDeleteView(LoginRequiredMixin, DeleteView):
    """Allow authenticated users to delete a ranking."""

    model = Ranking
    template_name = "ranking/ranking_confirm_delete.html"
    success_url = reverse_lazy("ranking:list")
