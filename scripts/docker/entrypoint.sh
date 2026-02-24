#!/bin/sh
# Gunicorn entrypoint — overridable via Container App environment variables.
#
# Why a shell script instead of a JSON-array ENTRYPOINT?
# JSON-array form bypasses the shell, so environment variable expansion
# (${GUNICORN_WORKERS}) is not available. A shell script lets the Container
# App environment override these values per environment without rebuilding
# the image.
#
# Worker class: gevent
# gevent monkey-patches the Python standard library so that blocking calls
# (time.sleep, socket I/O) yield to the event loop instead of occupying the
# OS thread. This is required for long-lived connections such as the SSE
# endpoint at mammograms:appointment_images_stream. Without an async worker
# class, each SSE connection permanently blocks a sync worker, exhausting the
# worker pool and causing liveness probe failures.
#
# Env vars (set in Azure Container Apps to override per environment):
#   GUNICORN_WORKERS            — number of worker processes (default 2)
#   GUNICORN_WORKER_CONNECTIONS — max simultaneous connections per worker (default 1000)
#   GUNICORN_TIMEOUT            — worker silent timeout in seconds (default 120)
#   GUNICORN_MAX_REQUESTS       — requests per worker before graceful restart; prevents
#                                 memory leaks accumulating indefinitely (default 1000)
#   GUNICORN_MAX_REQUESTS_JITTER — random offset added to max_requests per worker so
#                                 restarts are staggered, avoiding a thundering herd
#                                 (default 100)

exec /app/.venv/bin/gunicorn \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-2}" \
  --worker-class gevent \
  --worker-connections "${GUNICORN_WORKER_CONNECTIONS:-1000}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --max-requests "${GUNICORN_MAX_REQUESTS:-1000}" \
  --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-100}" \
  manage_breast_screening.config.wsgi
