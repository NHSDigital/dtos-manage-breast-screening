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
CMAPI_CONSUMER_KEY=some-consumer
PERSONAS_ENABLED=1

# CIS2 / Authlib
CIS2_SERVER_METADATA_URL=
CIS2_CLIENT_ID=
# Private key for private_key_jwt: provide PEM as env var (escape newlines as \n)
CIS2_PRIVATE_KEY=
# Scopes to request
CIS2_SCOPES="openid profile"
