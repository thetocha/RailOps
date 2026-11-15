from django.apps import AppConfig


class IncidentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.incidents"
    label = "incidents"
    verbose_name = "Incidents"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.incidents.signals import seed_incident_permissions_on_migrate

        post_migrate.connect(
            seed_incident_permissions_on_migrate,
            sender=self,
            dispatch_uid="incidents.seed_permissions",
        )
