"""Idempotent role-group seeder. Safe to re-run."""

from __future__ import annotations

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from apps.accounts.permissions import (
    assign_administrator_group_to_superusers,
    ensure_role_groups,
)


class Command(BaseCommand):
    help = (
        "Create Administrator, Dispatcher, and Viewer groups and assign the "
        "accounts.user permissions catalog. Idempotent."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--assign-superusers",
            action="store_true",
            help="Add every superuser to the Administrator group and set is_staff.",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        ensure_role_groups()
        self.stdout.write(self.style.SUCCESS("Role groups ensured."))
        if options["assign_superusers"]:
            assigned = assign_administrator_group_to_superusers()
            self.stdout.write(
                self.style.SUCCESS(f"Assigned Administrator group to {assigned} superuser(s).")
            )
