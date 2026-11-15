from django.urls import path

from apps.integrations import views

urlpatterns = [
    path("integrations/sync-runs/", views.SyncRunListView.as_view(), name="sync_run_list"),
    path("integrations/sync-runs/run/", views.TimetableSyncView.as_view(), name="timetable_sync"),
]
