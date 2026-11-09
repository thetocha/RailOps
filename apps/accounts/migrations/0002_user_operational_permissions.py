from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial_custom_user"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "permissions": [
                    ("manage_users", "Can manage users and assign roles"),
                    ("access_dashboard", "Can access the operations dashboard"),
                    ("view_operations", "Can view operational records"),
                    (
                        "change_operations",
                        "Can create and update operational records",
                    ),
                ],
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
    ]
