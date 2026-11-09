# Generated for unique non-blank emails on accounts.User.

from typing import Any

from django.db import migrations, models


def disambiguate_duplicate_emails(apps: Any, schema_editor: Any) -> None:
    """Keep the first row per email; suffix later duplicates so the index can apply."""
    user_model = apps.get_model("accounts", "User")
    seen: dict[str, int] = {}
    for user in user_model.objects.exclude(email="").order_by("pk").iterator():
        email = user.email
        if email not in seen:
            seen[email] = user.pk
            continue
        local, separator, domain = email.partition("@")
        candidate = f"{local}+dup{user.pk}@{domain}" if separator else f"dup{user.pk}-{email}"
        user.email = candidate[:254]
        user.save(update_fields=["email"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_operational_permissions"),
    ]

    operations = [
        migrations.RunPython(disambiguate_duplicate_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                condition=models.Q(("email", ""), _negated=True),
                fields=("email",),
                name="accounts_user_unique_email",
            ),
        ),
    ]
