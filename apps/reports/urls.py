from django.urls import path

from apps.reports import views

urlpatterns = [
    path("reports/", views.ReportListView.as_view(), name="report_list"),
    path("reports/create/", views.ReportCreateView.as_view(), name="report_create"),
    path("reports/<uuid:pk>/", views.ReportDetailView.as_view(), name="report_detail"),
    path("reports/<uuid:pk>/download/", views.ReportDownloadView.as_view(), name="report_download"),
]
