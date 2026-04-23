# Base settings shared across all environments.
# This file does not call load_dotenv; env vars must be populated before it is imported.

import sys
from os import environ
from pathlib import Path

from jinja2 import ChainableUndefined


def boolean_env(key, default=None):
    value = environ.get(key)
    if value is None:
        return default
    return value in ("True", "true", "1")


def list_env(key):
    value = environ.get(key)
    return value.split(",") if value else []


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Strip whitespace from all env vars to avoid issues with stray \r\n from Key Vault
for key in environ:
    environ[key] = environ[key].strip()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = boolean_env("DEBUG", default=False)

DJANGO_ENV = environ.get("DJANGO_ENV", "production")

ALLOWED_HOSTS = list_env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = list_env("CSRF_TRUSTED_ORIGINS")

CSRF_COOKIE_SECURE = boolean_env("CSRF_COOKIE_SECURE", default=True)
SESSION_COOKIE_SECURE = boolean_env("SESSION_COOKIE_SECURE", default=True)
# SECURE_SSL_REDIRECT is set to False because TLS termination is handled at the Azure Container Apps layer
SECURE_SSL_REDIRECT = False

SERVICE_ENABLED = boolean_env("SERVICE_ENABLED", default=True)

# SECURITY WARNING: don't run with PERSONAS_ENABLED turned on in production!
PERSONAS_ENABLED = boolean_env("PERSONAS_ENABLED", default=False)

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "manage_breast_screening.users",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.postgres",
    "django.forms",
    "qsessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django_linear_migrations",
    "manage_breast_screening.core",
    "manage_breast_screening.auth",
    "manage_breast_screening.clinics",
    "manage_breast_screening.dicom",
    "manage_breast_screening.nhsuk_forms",
    "manage_breast_screening.participants",
    "manage_breast_screening.mammograms",
    "manage_breast_screening.manual_images",
    "manage_breast_screening.gateway",
    "rules.apps.AutodiscoverRulesConfig",
    "csp",
]

if DJANGO_ENV != "production":
    INSTALLED_APPS.append("manage_breast_screening.nonprod")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "manage_breast_screening.core.middleware.exception_logging.CorrelationIdMiddleware",
    "manage_breast_screening.core.middleware.service_enabled.ServiceEnabledMiddleware",
    "manage_breast_screening.core.middleware.exception_logging.ExceptionLoggingMiddleware",
    "manage_breast_screening.core.middleware.robots.RobotsTagMiddleware",
    "manage_breast_screening.core.middleware.basic_auth.BasicAuthMiddleware",
    "qsessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "manage_breast_screening.core.middleware.auth.ManageAuthenticationMiddleware",
    "manage_breast_screening.core.middleware.auth.ManageLoginRequiredMiddleware",
    "manage_breast_screening.core.middleware.session_timeout.SessionTimeoutMiddleware",
    "manage_breast_screening.core.middleware.current_provider.CurrentProviderMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "ninja.compatibility.files.fix_request_files_middleware",
    "csp.middleware.CSPMiddleware",
]

if DEBUG:
    INTERNAL_IPS = ["127.0.0.1"]  # gitleaks:allow

DEBUG_TOOLBAR = DEBUG
if DEBUG_TOOLBAR:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = ("manage_breast_screening.auth.backends.CIS2Backend",)

ROOT_URLCONF = "manage_breast_screening.core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "jinja2"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "manage_breast_screening.config.jinja2_env.environment",
            "context_processors": [
                "manage_breast_screening.core.context_processors.nav_active",
            ],
            "undefined": ChainableUndefined,
            "trim_blocks": True,
            "lstrip_blocks": True,
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    },
]

WSGI_APPLICATION = "manage_breast_screening.config.wsgi.application"
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

SESSION_ENGINE = "qsessions.backends.db"
SESSION_COOKIE_AGE = 43200  # 12 hours
SESSION_INACTIVITY_TIMEOUT = 900  # 15 minutes - logout after inactivity
SESSION_ACTIVITY_UPDATE_THRESHOLD = (
    60  # Update last_activity every 60s to reduce DB writes
)
SESSION_HARD_TIMEOUT = 43200  # 12 hours - absolute session limit

COMMIT_SHA = environ.get("COMMIT_SHA", "")

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "manage_breast_screening.config.postgresql",
        "NAME": environ.get("DATABASE_NAME", ""),
        "USER": environ.get("DATABASE_USER", ""),
        "PASSWORD": environ.get("DATABASE_PASSWORD", ""),
        "HOST": environ.get("DATABASE_HOST", ""),
        "PORT": environ.get("DATABASE_PORT", "5432"),
        "OPTIONS": {"sslmode": environ.get("DATABASE_SSLMODE", "prefer")},
        "TIME_ZONE": "Europe/London",
        # The pod authenticates to PostgreSQL via Azure AD managed identity (DefaultAzureCredential).
        # Tokens last ~60-75 minutes. CONN_MAX_AGE must be shorter than the token lifetime to avoid reusing connections with expired tokens.
        "CONN_MAX_AGE": int(environ.get("DATABASE_CONN_MAX_AGE", "0")),
        "CONN_HEALTH_CHECKS": True,
    }
}


if DJANGO_ENV != "production":
    if environ.get("BLOB_STORAGE_CONNECTION_STRING"):
        # Use connection string if provided (e.g., in local development using Azurite)
        dicom_storage_options = {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": {
                "connection_string": environ.get("BLOB_STORAGE_CONNECTION_STRING"),
                "azure_container": "dicom",
            },
        }
    else:
        # In non-production environments without a connection string, use local file storage
        dicom_storage_options = {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "location": BASE_DIR / "data" / "dicom",
                "base_url": "/dicom/",
            },
        }
else:
    # In production, authenticate to Azure Blob Storage using managed identity.
    dicom_storage_options = {
        "BACKEND": "manage_breast_screening.config.azure_blob_storage.ManagedIdentityAzureStorage",
        "OPTIONS": {
            "account_name": environ.get("STORAGE_ACCOUNT_NAME"),
            "azure_container": "dicom",
        },
    }

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "dicom": dicom_storage_options,
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/London"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [BASE_DIR / "static", BASE_DIR / "assets" / "compiled"]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field


ROOT_LOG_LEVEL = environ.get("LOG_LEVEL", "INFO").upper()
LOG_QUERIES = boolean_env("LOG_QUERIES")
LOGGING = {
    "version": 1,  # the dictConfig format version
    "disable_existing_loggers": False,  # retain the default loggers
    "filters": {
        "correlation_id": {
            "()": "manage_breast_screening.core.middleware.exception_logging.CorrelationIdFilter",
        },
        "suppress_duplicate_exceptions": {
            "()": "manage_breast_screening.core.middleware.exception_logging.SuppressDuplicateExceptionFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(process)d] [%(levelname)s] [%(correlation_id)s] [%(module)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stdout,
            "filters": ["correlation_id"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": ROOT_LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "level": "INFO",
        },
        "django.request": {
            "filters": ["suppress_duplicate_exceptions"],
        },
        "django.db.backends": {
            "level": "DEBUG" if LOG_QUERIES else "INFO",
        },
        "faker": {"level": "INFO"},
        "msal": {"level": "INFO"},
        "azure.monitor.opentelemetry": {"level": "WARNING"},
        "azure.core.pipeline.policies.http_logging_policy": {"level": "WARNING"},
    },
}

AUDIT_EXCLUDED_FIELDS = ["password", "token", "created_at", "updated_at", "id"]

if PERSONAS_ENABLED:
    LOGIN_URL = "auth:persona_login"
else:
    LOGIN_URL = "auth:login"

# CIS2 / Authlib configuration
# These settings configure Authlib's Django client to use CIS2 via private_key_jwt
CIS2_SERVER_METADATA_URL = environ.get("CIS2_SERVER_METADATA_URL")
CIS2_CLIENT_ID = environ.get("CIS2_CLIENT_ID")
# Load the private key used for private_key_jwt from environment (PEM format). Newlines may be provided as \n.
private_key_inline = environ.get("CIS2_CLIENT_PRIVATE_KEY")
CIS2_CLIENT_PRIVATE_KEY = (
    private_key_inline.replace("\\n", "\n") if private_key_inline else None
)
CIS2_SCOPES = "openid profile email nhsperson associatedorgs"
CIS2_DEBUG = boolean_env("CIS2_DEBUG", default=False)
# Sent to CIS2 authorization endpoint during auth process
# Determines the authentication options available to the user (authenticator app, smart card, etc.)
# Use either "AAL3_ANY" or "AAL2_OR_AAL3_ANY"
CIS2_ACR_VALUES = environ.get("CIS2_ACR_VALUES", default="AAL3_ANY")
# Minimum identity assurance level required for CIS2 authentication
CIS2_REQUIRED_ID_ASSURANCE_LEVEL = 3

BASE_URL = environ.get("BASE_URL")

# HTTP Basic Auth (optional; off by default)
BASIC_AUTH_ENABLED = boolean_env("BASIC_AUTH_ENABLED", default=False)
BASIC_AUTH_USERNAME = environ.get("BASIC_AUTH_USERNAME")
BASIC_AUTH_PASSWORD = environ.get("BASIC_AUTH_PASSWORD")
BASIC_AUTH_REALM = environ.get("BASIC_AUTH_REALM", "Restricted")

API_PATH_PREFIX = "/api/"
ADMIN_PATH_PREFIX = "/admin/"

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
# tells Django to trust the X-Forwarded-Proto header that comes from our proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Prevent the browser from guessing content types
SECURE_CONTENT_TYPE_NOSNIFF = True

# Referrer policy for enhanced privacy
SECURE_REFERRER_POLICY = "same-origin"

# Session and CSRF cookie security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True

CSP_SELF = "'self'"
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "base-uri": (CSP_SELF,),
        "connect-src": (CSP_SELF,),
        "default-src": (CSP_SELF,),
        "font-src": (CSP_SELF, "https://assets.nhs.uk"),
        "form-action": (CSP_SELF,),
        "frame-ancestors": ("'none'",),
        "img-src": (CSP_SELF, "data:"),
        "object-src": ("'none'",),
        "script-src": (CSP_SELF, "'unsafe-inline'"),
        "style-src": (CSP_SELF,),
    }
}

READING_SESSION_DEFAULT_SIZE = 50
