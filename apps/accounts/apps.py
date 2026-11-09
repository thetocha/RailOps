from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
    verbose_name = "Accounts"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.accounts.signals import seed_role_groups_on_migrate

        post_migrate.connect(
            seed_role_groups_on_migrate,
            sender=self,
            dispatch_uid="accounts.seed_role_groups",
        )
