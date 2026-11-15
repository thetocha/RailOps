from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import IsAuthenticated
from rest_framework.routers import DefaultRouter

from apps.incidents.api.views import IncidentViewSet
from apps.infrastructure.api.views import StationViewSet
from apps.timetables.api.views import TrainServiceViewSet

router = DefaultRouter()
router.register("stations", StationViewSet, basename="api-station")
router.register("incidents", IncidentViewSet, basename="api-incident")
router.register("services", TrainServiceViewSet, basename="api-service")

urlpatterns = [
    path(
        "schema/",
        SpectacularAPIView.as_view(permission_classes=[IsAuthenticated]),
        name="api-schema",
    ),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(
            url_name="api-schema",
            permission_classes=[IsAuthenticated],
        ),
        name="api-docs",
    ),
    path("v1/", include(router.urls)),
]
