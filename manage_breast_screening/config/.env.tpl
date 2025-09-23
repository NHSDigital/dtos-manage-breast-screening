SECRET_KEY="django-insecure-rqrslm6t05zphv(-j(k4*ri$ua8u1d8hg827w!m21+viul_hw&"
DEBUG=True
ALLOWED_HOSTS="localhost,127.0.0.1"
GUNICORN_CMD_ARGS="--log-level DEBUG"
DATABASE_NAME=manage
DATABASE_PASSWORD=changeme
DATABASE_USER=manage
DATABASE_SSLMODE=allow
DATABASE_HOST=localhost
LOG_QUERIES=0
PERSONAS_ENABLED=1

# Set to FQDN in deployed environments
BASE_URL=http://localhost:8000

# CIS2 / Authlib
CIS2_SERVER_METADATA_URL=changeme
CIS2_CLIENT_ID=changeme
# Private key in PEM format (paste a multiline string)
CIS2_CLIENT_PRIVATE_KEY="paste-pem-private-key-here"
# Public key in PEM format (paste a multiline string)
CIS2_CLIENT_PUBLIC_KEY="paste-pem-public-key-here"
# Toggle debug logging for CIS2
CIS2_DEBUG=False

NOTIFICATIONS_BATCH_RETRY_LIMIT=5
NOTIFICATIONS_BATCH_RETRY_DELAY=10

BASIC_AUTH_ENABLED=False
BASIC_AUTH_USERNAME=changeme
BASIC_AUTH_PASSWORD=changeme

