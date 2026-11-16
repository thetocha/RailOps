from __future__ import annotations

from unittest.mock import patch

from scripts.release import run_release


def test_release_stops_when_database_is_unavailable() -> None:
    with (
        patch("scripts.release.wait_for_database", return_value=1) as wait,
        patch("scripts.release.django.setup") as setup,
        patch("scripts.release.call_command") as call,
    ):
        assert run_release() == 1
    wait.assert_called_once()
    setup.assert_not_called()
    call.assert_not_called()


def test_release_migrates_then_collects_static() -> None:
    with (
        patch("scripts.release.wait_for_database", return_value=0),
        patch("scripts.release.django.setup"),
        patch("scripts.release.call_command") as call,
    ):
        assert run_release() == 0
    assert call.call_args_list[0].args[0] == "migrate"
    assert call.call_args_list[1].args[0] == "collectstatic"
