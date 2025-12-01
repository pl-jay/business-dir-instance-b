# apps/api/views.py
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Count, Avg, Q
from django.utils import timezone
from apps.directory.models import Business
from apps.reviews.models import ReviewSignature, Review
from apps.onchain.models import OnChainRecord

def api_businesses(request):
    ordering = request.GET.get("ordering")
    qs = Business.objects.all()
    if ordering == "avg_rating":
        qs = qs.annotate(avg=Avg("review__rating", filter=Q(review__is_hidden=False))).order_by("-avg","name")
    elif ordering == "reviews_30d":
        since = timezone.now() - timezone.timedelta(days=30)
        qs = qs.annotate(r30=Count("review", filter=Q(review__is_hidden=False, review__created_at__gte=since))).order_by("-r30","name")
    else:
        return HttpResponseBadRequest("unknown ordering")
    data = [{"name": b.name, "slug": b.slug} for b in qs[:100]]
    return JsonResponse({"results": data})

def api_business_onchain(request, slug):
    rows = list(OnChainRecord.objects.filter(business__slug=slug).values(
        "kind","review_id","chain","tx_hash","note","created_at"
    )[:200])
    return JsonResponse({"results": rows})

def api_review_signature_presence(request, pk):
    exists = ReviewSignature.objects.filter(review_id=pk).exists()
    return JsonResponse({"signed": exists})
