from django.urls import path

from apps.analytics import views

urlpatterns = [
    path("analytics/", views.AnalyticsOverviewView.as_view(), name="analytics_overview"),
]
