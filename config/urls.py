from django.contrib import admin
from django.urls import include, path

from config.health import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("", include("apps.accounts.urls")),
]
