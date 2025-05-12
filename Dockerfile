ARG poetry_version=2.1.2

#### NODE.JS BUILD

FROM node:24.0.0-alpine3.21@sha256:7804c7734b3e0cf647ab8273a1d4cda776123145da5952732f3dca9e742ddca0 AS node_builder

WORKDIR /app

# Install dependencies for npm install command
RUN apk add --no-cache bash

# Compile static assets
COPY package.json package-lock.json ./
COPY manage_breast_screening ./manage_breast_screening
RUN npm ci
RUN npm run compile

FROM python:3.13.3-alpine3.21@sha256:452682e4648deafe431ad2f2391d726d7c52f0ff291be8bd4074b10379bb89ff AS python_builder
ARG poetry_version

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Install python dependencies to a virtualenv
COPY pyproject.toml poetry.lock ./
RUN pip install poetry=="${poetry_version}"
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

#### FINAL RUNTIME IMAGE

FROM python:3.13.3-alpine3.21@sha256:452682e4648deafe431ad2f2391d726d7c52f0ff291be8bd4074b10379bb89ff


# Workaround for CVE-2024-6345 upgrade the installed version of setuptools to the latest version
RUN pip install -U setuptools

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

# Run django commands
ENV DEBUG=0
RUN python ./manage.py collectstatic --noinput

# Remove later once we've set up an external DB
RUN python ./manage.py migrate

EXPOSE 8000

ENTRYPOINT ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "manage_breast_screening.config.wsgi"]
