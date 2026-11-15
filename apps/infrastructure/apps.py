from django.apps import AppConfig


class InfrastructureConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.infrastructure"
    label = "infrastructure"
    verbose_name = "Infrastructure"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.infrastructure.signals import seed_infrastructure_permissions_on_migrate

        post_migrate.connect(
            seed_infrastructure_permissions_on_migrate,
            sender=self,
            dispatch_uid="infrastructure.seed_permissions",
        )
