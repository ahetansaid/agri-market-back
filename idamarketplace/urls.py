"""
URL configuration — Backend Django headless.

Le frontend HTML (templates + static custom) a ete retire lors de la
separation en Session 1 Next.js. Cette config expose UNIQUEMENT :
  - /admin/       : administration Django (avec 2FA en prod)
  - /account/     : endpoints 2FA (two_factor : setup, verify, disable)
  - /api/*        : API REST consommee par Next.js frontend
  - /api/docs/    : Swagger UI (documentation OpenAPI)
  - /api/redoc/   : Redoc UI

Le frontend public (home, listing, detail, dashboards, auth) tourne
maintenant en Next.js sur agri-market-frontend.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as media_serve

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from two_factor.admin import AdminSiteOTPRequired
from two_factor.urls import urlpatterns as tf_urls

from accounts.api import (
    activate_account,
    me,
    my_announcements,
    my_ratings,
    password_reset_confirm,
    password_reset_request,
    register,
    support_messages,
    support_unread,
)
from evenements.api import EvenementViewSet
from marketplace.api import (
    AnnouncementViewSet,
    CategoryViewSet,
    announcement_conversation,
    conversation_detail,
    conversations_unread,
    countries_activity,
    create_announcement,
    my_conversations,
    producer_of_month,
    spotlight_category,
    stats_summary,
)


class _AuthRateThrottle(AnonRateThrottle):
    """Limite anti brute-force sur token obtain/refresh."""

    scope = "auth"


class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [_AuthRateThrottle]


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [_AuthRateThrottle]


# Force la 2FA pour l'admin en production. En DEV (DEBUG=True), la 2FA
# reste optionnelle pour faciliter les tests locaux.
# 2FA obligatoire pour l'admin en prod, desactivable via ADMIN_REQUIRE_2FA=False
# (utile le temps d'enroler son application TOTP).
import os as _os  # noqa: E402

if (
    not settings.DEBUG
    and _os.getenv("ADMIN_REQUIRE_2FA", "True").strip().lower() != "false"
):
    admin.site.__class__ = AdminSiteOTPRequired


# Router DRF : ViewSets marketplace + evenements
router = DefaultRouter()
router.register(r"api/announcements", AnnouncementViewSet, basename="announcement")
router.register(r"api/categories", CategoryViewSet, basename="category")
router.register(r"api/evenements", EvenementViewSet)


urlpatterns = [
    # ==========================================================
    # ADMIN Django (+ 2FA endpoints pour setup/verify)
    # ==========================================================
    path("admin/", admin.site.urls),
    # two_factor.urls contient DEJA le prefixe "account/" : l'inclure sous
    # "account/" donnait /account/account/login/ (et LOGIN_URL pointait vers
    # un 404) -> l'admin etait inaccessible en prod.
    path("", include(tf_urls)),
    # Upload de fichiers des champs texte riche (admin blog/evenements).
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    # ==========================================================
    # API REST — consommee par Next.js frontend
    # ==========================================================
    # Auth JWT
    path(
        "api/auth/token/",
        ThrottledTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/auth/token/refresh/",
        ThrottledTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("api/auth/register/", register, name="api-register"),
    path("api/auth/activate/", activate_account, name="api-activate"),
    path(
        "api/auth/password-reset/",
        password_reset_request,
        name="api-password-reset",
    ),
    path(
        "api/auth/password-reset/confirm/",
        password_reset_confirm,
        name="api-password-reset-confirm",
    ),
    # User endpoints
    path("api/me/", me, name="api-me"),
    path("api/me/announcements/", my_announcements, name="api-me-announcements"),
    path(
        "api/me/announcements/create/",
        create_announcement,
        name="api-create-announcement",
    ),
    path("api/me/ratings/", my_ratings, name="api-me-ratings"),
    path("api/me/conversations/", my_conversations, name="api-me-conversations"),
    path(
        "api/me/conversations/unread/",
        conversations_unread,
        name="api-me-conversations-unread",
    ),
    path("api/support/messages/", support_messages, name="api-support-messages"),
    path("api/support/unread/", support_unread, name="api-support-unread"),
    # Messagerie acheteur <-> vendeur
    path(
        "api/announcements/<int:pk>/messages/",
        announcement_conversation,
        name="api-announcement-conversation",
    ),
    path(
        "api/conversations/<int:pk>/",
        conversation_detail,
        name="api-conversation-detail",
    ),
    # Meta endpoints (stats & geo)
    path("api/stats/summary/", stats_summary, name="api-stats-summary"),
    path("api/countries/activity/", countries_activity, name="api-countries-activity"),
    path("api/producer-of-month/", producer_of_month, name="api-producer-of-month"),
    path("api/spotlight-category/", spotlight_category, name="api-spotlight-category"),
    # ViewSets (annonces, categories, evenements)
    path("", include(router.urls)),
    # Documentation OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Sert /media/ meme en production (staging) : les images produits sont
# versionnees dans le repo. Pour du durable -> stockage objet (S3/R2).
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        media_serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
