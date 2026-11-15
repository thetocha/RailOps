from django.urls import path

from apps.timetables import views

urlpatterns = [
    path("services/", views.TrainServiceListView.as_view(), name="train_service_list"),
    path(
        "services/<uuid:pk>/",
        views.TrainServiceDetailView.as_view(),
        name="train_service_detail",
    ),
]
