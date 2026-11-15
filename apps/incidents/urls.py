from django.urls import path

from apps.incidents import views

urlpatterns = [
    path("incidents/", views.IncidentListView.as_view(), name="incident_list"),
    path("incidents/create/", views.IncidentCreateView.as_view(), name="incident_create"),
    path("incidents/<uuid:pk>/", views.IncidentDetailView.as_view(), name="incident_detail"),
    path("incidents/<uuid:pk>/edit/", views.IncidentUpdateView.as_view(), name="incident_update"),
    path(
        "incidents/<uuid:pk>/transition/",
        views.IncidentTransitionView.as_view(),
        name="incident_transition",
    ),
    path(
        "incidents/<uuid:pk>/assign/",
        views.IncidentAssignView.as_view(),
        name="incident_assign",
    ),
    path(
        "incidents/<uuid:pk>/severity/",
        views.IncidentSeverityView.as_view(),
        name="incident_severity",
    ),
]
