"""
URL configuration for the patriot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('home/', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('home/', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Directory app routes (namespaced)
    path("", include(("apps.directory.urls", "apps.directory"), namespace="directory")),
    # Authentication (login, logout, password reset) using Django's built‑in views
    path("accounts/login/",  auth_views.LoginView.as_view(),  name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Other apps
    path("onchain/", include(("apps.onchain.urls", "apps.onchain"), namespace="onchain")),
    path("promotions/", include("apps.promotions.urls", namespace="promotions")),

    path("ranking/", include(("apps.ranking.urls", "apps.ranking"), namespace="ranking")),

    path("reviews/", include(("apps.reviews.urls", "apps.reviews"), namespace="reviews")),
    path("api/reviews/", include("apps.reviews.api_urls")),

    path("users/", include(("apps.usersapp.urls", "apps.usersapp"), namespace="usersapp")),

    path("api/wallet/", include("apps.wallets.urls")),
    path("api/", include("apps.api.urls")),
    path("accounts/", include("apps.accounts.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
