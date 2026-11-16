# syntax=docker/dockerfile:1.7

FROM python:3.13.14-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:/usr/local/bin:$PATH"

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.13.14-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /usr/sbin/nologin railops \
    && mkdir -p /app/media /app/staticfiles

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

COPY --chown=railops:railops manage.py pyproject.toml uv.lock ./
COPY --chown=railops:railops config ./config
COPY --chown=railops:railops apps ./apps
COPY --chown=railops:railops templates ./templates
COPY --chown=railops:railops static ./static
COPY --chown=railops:railops scripts ./scripts

RUN DJANGO_SETTINGS_MODULE=config.settings.staticbuild \
    python manage.py collectstatic --noinput \
    && chown -R railops:railops /app /opt/venv

USER railops

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=5)"

CMD ["gunicorn", "--config", "config/gunicorn.conf.py", "config.wsgi:application"]
