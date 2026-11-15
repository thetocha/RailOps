from django.apps import AppConfig


class TimetablesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.timetables"
    label = "timetables"
    verbose_name = "Timetables"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from apps.timetables.signals import seed_timetable_permissions_on_migrate

        post_migrate.connect(
            seed_timetable_permissions_on_migrate,
            sender=self,
            dispatch_uid="timetables.seed_permissions",
        )
