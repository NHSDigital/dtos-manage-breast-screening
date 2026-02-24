#### NODE.JS BUILD

FROM node:22.20-alpine3.21@sha256:f40aebdd0c1959821ab6d72daecafb2cd1d4c9a958e9952c1d71b84d4458f875 AS node_builder

WORKDIR /app

# Install dependencies for npm ci command
RUN apk add --no-cache bash

# Compile static assets
COPY .browserslistrc babel.config.cjs package.json package-lock.json rollup.config.js  ./
COPY manage_breast_screening/assets ./manage_breast_screening/assets
RUN npm ci
RUN npm run compile

FROM python:3.14.0-alpine3.21@sha256:f1ac9e01293a18a24919826ea8c7bb8f7bbc25497887a0a1cade58801bb83d1c AS python_builder

WORKDIR /app

RUN apk add --no-cache libgcc libstdc++ build-base linux-headers

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_CACHE_DIR=/tmp/uv_cache

# Install python dependencies to a virtualenv
COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /uvx /bin/
RUN uv sync --frozen --no-dev --compile-bytecode --no-editable && rm -rf $UV_CACHE_DIR

#### FINAL RUNTIME IMAGE

FROM python:3.14.0-alpine3.21@sha256:f1ac9e01293a18a24919826ea8c7bb8f7bbc25497887a0a1cade58801bb83d1c

# Use a non-root user
ENV CONTAINER_USER=appuser \
    CONTAINER_GROUP=appuser \
    CONTAINER_UID=31337 \
    CONTAINER_GID=31337

RUN addgroup --gid ${CONTAINER_GID} --system ${CONTAINER_GROUP} \
    && adduser --uid ${CONTAINER_UID} --system ${CONTAINER_USER} --ingroup ${CONTAINER_GROUP}

USER ${CONTAINER_UID}
WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=python_builder --chown=${CONTAINER_USER}:${CONTAINER_GROUP} ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --chown=${CONTAINER_USER}:${CONTAINER_GROUP} ./manage_breast_screening /app/manage_breast_screening
COPY --from=node_builder --chown=${CONTAINER_USER}:${CONTAINER_GROUP} /app/manage_breast_screening/assets/compiled /app/manage_breast_screening/assets/compiled
COPY --chown=${CONTAINER_USER}:${CONTAINER_GROUP} manage.py ./
COPY --chown=root:root --chmod=755 scripts/docker/entrypoint.sh /app/entrypoint.sh

# Run django commands
ENV DEBUG=0
RUN python ./manage.py collectstatic --noinput

EXPOSE 8000

ARG COMMIT_SHA
ENV COMMIT_SHA=$COMMIT_SHA

# Gunicorn tuning — overridable per environment via Container App environment variables
ENV GUNICORN_WORKERS=2 \
    GUNICORN_WORKER_CONNECTIONS=1000 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_MAX_REQUESTS=1000 \
    GUNICORN_MAX_REQUESTS_JITTER=100

ENTRYPOINT ["/app/entrypoint.sh"]
