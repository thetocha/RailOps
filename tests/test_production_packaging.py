from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_is_multi_stage_non_root_gunicorn() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.13.14-slim-bookworm AS builder" in dockerfile
    assert "FROM python:3.13.14-slim-bookworm AS runtime" in dockerfile
    assert "uv sync --frozen --no-dev" in dockerfile
    assert "--all-groups" not in dockerfile
    assert "USER railops" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "collectstatic" in dockerfile
    assert "config.settings.staticbuild" in dockerfile
    assert 'CMD ["gunicorn"' in dockerfile
    assert "migrate" not in dockerfile
    assert "runserver" not in dockerfile


def test_production_compose_keeps_migrate_off_workers() -> None:
    compose = (ROOT / "compose.production.yaml").read_text(encoding="utf-8")
    assert '["python", "-m", "scripts.release"]' in compose
    assert "config/gunicorn.conf.py" in compose
    assert "runserver" not in compose
    assert "nginx:1.28.0-alpine" in compose
    assert compose.index("release:") < compose.index("\n  app:")


def test_nginx_does_not_serve_media_or_enable_autoindex() -> None:
    nginx = (ROOT / "deploy/nginx/default.conf").read_text(encoding="utf-8")
    assert "server_tokens off" in nginx
    assert "autoindex" not in nginx
    assert "location /static/" in nginx
    assert "location /health/" in nginx
    assert "location /media/" not in nginx
    assert "proxy_set_header X-Forwarded-Proto $forwarded_proto" in nginx
    assert "map $http_x_forwarded_proto $forwarded_proto" in nginx
    assert "client_max_body_size 2m" in nginx


def test_backup_script_does_not_put_password_on_argv() -> None:
    script = (ROOT / "scripts/backup_database.sh").read_text(encoding="utf-8")
    assert "pg_dump" in script
    assert "--no-password" in script
    assert "--password" not in script
    assert "PGPASSWORD=" not in script
    assert "DB_PASSWORD" not in script


def test_gunicorn_does_not_daemonize_or_migrate() -> None:
    source = (ROOT / "config/gunicorn.conf.py").read_text(encoding="utf-8")
    assert "daemon = False" in source
    assert "migrate" not in source
    assert 'accesslog = "-"' in source


def test_deploy_workflow_does_not_migrate_on_app_start() -> None:
    workflow = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "docker build" in workflow
    assert "gunicorn --check-config" in workflow
    assert "manage.py migrate" not in workflow
    assert "does not connect to a VPS" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow


def test_env_example_documents_production_runtime_knobs() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "GUNICORN_WORKERS" in text
    assert "NGINX_PUBLISH_PORT" in text
    assert "BACKUP_DIR" in text
