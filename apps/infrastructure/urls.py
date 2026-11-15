from django.urls import path

from apps.infrastructure import views

urlpatterns = [
    path("stations/", views.StationListView.as_view(), name="station_list"),
    path("stations/create/", views.StationCreateView.as_view(), name="station_create"),
    path("stations/<uuid:pk>/", views.StationDetailView.as_view(), name="station_detail"),
    path("stations/<uuid:pk>/edit/", views.StationUpdateView.as_view(), name="station_update"),
    path(
        "stations/<uuid:pk>/deactivate/",
        views.StationDeactivateView.as_view(),
        name="station_deactivate",
    ),
    path("lines/", views.RailwayLineListView.as_view(), name="railway_line_list"),
    path("lines/create/", views.RailwayLineCreateView.as_view(), name="railway_line_create"),
    path("lines/<uuid:pk>/", views.RailwayLineDetailView.as_view(), name="railway_line_detail"),
    path(
        "lines/<uuid:pk>/edit/",
        views.RailwayLineUpdateView.as_view(),
        name="railway_line_update",
    ),
    path(
        "lines/<uuid:pk>/deactivate/",
        views.RailwayLineDeactivateView.as_view(),
        name="railway_line_deactivate",
    ),
]
