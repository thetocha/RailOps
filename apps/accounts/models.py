from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user. `is_active` is inherited from AbstractUser; do not duplicate it.

    Roles are Django Groups (Administrator, Dispatcher, Viewer) seeded in
    `apps.accounts.permissions.ensure_role_groups`. Authorization checks must use
    Django permissions (see `apps.accounts.permissions`), not group-name tests.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        permissions = [
            ("manage_users", "Can manage users and assign roles"),
            ("access_dashboard", "Can access the operations dashboard"),
            ("view_operations", "Can view operational records"),
            ("change_operations", "Can create and update operational records"),
        ]

    def __str__(self) -> str:
        return self.get_username()
