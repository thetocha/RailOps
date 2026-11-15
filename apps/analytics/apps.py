from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.analytics"
    label = "analytics"
    verbose_name = "Analytics"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.analytics.signals import seed_analytics_permissions_on_migrate

        post_migrate.connect(
            seed_analytics_permissions_on_migrate,
            sender=self,
            dispatch_uid="analytics.seed_permissions",
        )
