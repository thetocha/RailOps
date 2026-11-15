from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations"
    label = "integrations"
    verbose_name = "Integrations"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.integrations.signals import seed_integration_permissions_on_migrate

        post_migrate.connect(
            seed_integration_permissions_on_migrate,
            sender=self,
            dispatch_uid="integrations.seed_permissions",
        )
