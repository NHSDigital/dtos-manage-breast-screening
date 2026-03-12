SECRET_KEY='django-insecure-rqrslm6t05zphv(-j(k4*ri$ua8u1d8hg827w!m21+viul_hw&'
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
# ACR values - determines which authentication options are available to users
# See https://digital.nhs.uk/services/care-identity-service/applications-and-services/cis2-authentication/guidance-for-developers/detailed-guidance/acr-values
CIS2_ACR_VALUES=AAL2_OR_AAL3_ANY
# Minimum identity assurance level required (1-3, where 3 is highest)
# See https://digital.nhs.uk/services/care-identity-service/applications-and-services/cis2-authentication/guidance-for-developers/detailed-guidance/scopes-and-claims
CIS2_REQUIRED_ID_ASSURANCE_LEVEL=3

BASIC_AUTH_ENABLED=False
BASIC_AUTH_USERNAME=changeme
BASIC_AUTH_PASSWORD=changeme
API_AUTH_TOKEN=changeme

# Django Ninja API
API_ENABLED=true
API_DOCS_ENABLED=true

# Automatic loading of PACS images from gateway
GATEWAY_IMAGES_ENABLED=False

APPLICATIONINSIGHTS_CONNECTION_STRING=""
APPLICATIONINSIGHTS_STATSBEAT_DISABLED_ALL=True
APPLICATIONINSIGHTS_LOGGER_NAME="insights-logger"
APPLICATIONINSIGHTS_IS_ENABLED=False
