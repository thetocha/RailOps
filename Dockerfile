FROM python:3.13.14-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:/root/.local/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.production

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        gdal-bin \
        libgdal-dev \
        libgeos-dev \
        libproj-dev \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --all-groups --no-install-project

COPY . .

RUN useradd --create-home --uid 1000 railops \
    && mkdir -p /app/media /app/staticfiles \
    && chown -R railops:railops /app /opt/venv

USER railops

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
