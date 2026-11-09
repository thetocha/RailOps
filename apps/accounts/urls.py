from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("accounts/login/", views.RailOpsLoginView.as_view(), name="login"),
    path("accounts/logout/", views.RailOpsLogoutView.as_view(), name="logout"),
    path(
        "accounts/password-change/",
        views.RailOpsPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "accounts/password-change/done/",
        views.RailOpsPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path(
        "accounts/password-reset/",
        views.RailOpsPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/done/",
        views.RailOpsPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        views.RailOpsPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        views.RailOpsPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("accounts/users/", views.UserListView.as_view(), name="user_list"),
    path("accounts/users/create/", views.UserCreateView.as_view(), name="user_create"),
    path(
        "accounts/users/<int:pk>/edit/",
        views.UserUpdateView.as_view(),
        name="user_update",
    ),
    path(
        "accounts/users/<int:pk>/deactivate/",
        views.UserDeactivateView.as_view(),
        name="user_deactivate",
    ),
]
