from django.urls import path
from . import views

app_name = "promotions"

urlpatterns = [
    path("", views.PromotionListView.as_view(), name="list"),
    path("<int:pk>/", views.promo_detail, name="detail"),
    path("<int:pk>/eligibility/", views.promo_eligibility_api, name="eligibility"),
    path("<int:pk>/claim/", views.promo_claim_api, name="claim"),
]
