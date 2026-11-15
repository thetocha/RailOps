from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reports"
    label = "reports"
    verbose_name = "Reports"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.reports.signals import seed_report_permissions_on_migrate

        post_migrate.connect(
            seed_report_permissions_on_migrate,
            sender=self,
            dispatch_uid="reports.seed_permissions",
        )
