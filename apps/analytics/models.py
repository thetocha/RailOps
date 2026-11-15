from django.db import models


class OperationalAnalytics(models.Model):
    """Permission carrier. Analytics are computed, not stored as rows."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_operationalanalytics", "Can view operational analytics"),
        ]

    def __str__(self) -> str:
        return "Operational analytics"
