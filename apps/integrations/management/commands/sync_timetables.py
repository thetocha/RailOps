"""Trigger timetable synchronization. Idempotent. Safe to re-run."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.integrations.models import ExternalSyncRun
from apps.integrations.services import build_provider, synchronize_timetables


class Command(BaseCommand):
    help = "Import timetable data from mock, CSV, or the configured HTTP endpoint."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--provider",
            choices=("mock", "csv", "http"),
            default="mock",
        )
        parser.add_argument(
            "--path",
            type=Path,
            help="CSV path (required when --provider=csv).",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        provider_name = str(options["provider"])
        csv_path = options.get("path")
        if provider_name == "csv" and csv_path is None:
            raise CommandError("--path is required for the CSV provider.")
        try:
            provider = build_provider(name=provider_name, csv_path=csv_path)
            run = synchronize_timetables(provider=provider)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"{run.integration_name} {run.status}: "
                f"processed={run.records_processed} created={run.records_created} "
                f"updated={run.records_updated}"
            )
        )
        if run.error_summary:
            self.stdout.write(run.error_summary)
        if run.status == ExternalSyncRun.Status.FAILED:
            raise CommandError("Synchronization failed.")
