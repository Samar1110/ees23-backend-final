from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic.base import TemplateView

admin.site.site_header = "Udyam Site Backend Administration"

schema_view = get_schema_view(
    openapi.Info(
        title="Udyam Site API",
        default_version="v1",
        description="This is the Udyam Site API.",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "broadcastMail",
        TemplateView.as_view(template_name="broadcastMail.html"),
        name="broadcastMail",
    ),
    path("auth/", include("customauth.urls")),
    path("api/", include("udyamHelper.urls")),
    path(r"^ckeditor/", include("ckeditor_uploader.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    # swagger API pages not visible on production
    urlpatterns += [
        path(
            "",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path(
            "auth/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path(
            "redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
        ),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
