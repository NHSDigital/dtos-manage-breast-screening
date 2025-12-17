SECRET_KEY="django-insecure-rqrslm6t05zphv(-j(k4*ri$ua8u1d8hg827w!m21+viul_hw&"
DEBUG=True
DJANGO_ENV=local
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

BASIC_AUTH_ENABLED=False
BASIC_AUTH_USERNAME=changeme
BASIC_AUTH_PASSWORD=changeme

# Notifications specific env vars
NOTIFICATIONS_BATCH_RETRY_LIMIT=5

API_OAUTH_API_KEY=""
API_OAUTH_API_KID=""
API_OAUTH_PRIVATE_KEY=""
API_OAUTH_TOKEN_URL=""
BLOB_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
BLOB_CONTAINER_NAME="notifications-mesh-data"
NBSS_MESH_INBOX_NAME="paste-mesh-inbox-name-here"
NBSS_MESH_PASSWORD="paste-mesh-password-here"
NBSS_MESH_CERT="paste-pem-mesh-cert-here"
NBSS_MESH_PRIVATE_KEY="paste-pem-private-key-here"
QUEUE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
REPORTS_CONTAINER_NAME="notifications-reports"
RETRY_QUEUE_NAME="notifications-message-batch-retries"

APPLICATIONINSIGHTS_CONNECTION_STRING=""
APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL=True
APPLICATIONINSIGHTS_LOGGER_NAME="manbrs-notifications"
APPLICATIONINSIGHTS_IS_ENABLED=False
