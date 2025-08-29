resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = var.region
}

module "shared_config" {
  source = "../dtos-devops-templates/infrastructure/modules/shared-config"

  env         = var.environment
  location    = var.region
  application = var.app_short_name
}

# populate the database
module "db_setup" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-dbm-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  # Run everything through /bin/sh
  container_command = ["/bin/sh", "-c"]

  # Build the full command string, conditionally including example_data
  # && python manage.py example_data"
  container_args = [
    var.env_config == "prod"
    ? "python manage.py migrate"
    : "python manage.py migrate && python manage.py seed_demo_data --noinput"
  ]

  docker_image               = var.docker_image
  user_assigned_identity_ids = [module.db_connect_identity.id]

  environment_variables = local.db_setup_env_vars
}

locals {
  # Convenience aliases so we don't repeat [0] everywhere
  postgres        = module.postgres[0]
  webapp_database = module.webapp_database[0]

  # Common name prefix for this app/env
  name_prefix = "${var.app_short_name}-${var.environment}"

  # Common environment variables shared across apps
  common_env = {
    SSL_MODE         = "require"
    AZURE_CLIENT_ID  = module.db_connect_identity.client_id
    PERSONAS_ENABLED = var.personas_enabled ? "1" : "0"
    DJANGO_ENV       = var.env_config
  }

  # --- Database setup job environment ---
  container_db_env = {
    DATABASE_HOST = local.webapp_database.container_app_fqdn
    DATABASE_NAME = "manage_breast_screening"
    DATABASE_USER = "admin"
  }

  vm_db_env = {
    DATABASE_HOST = local.postgres.host
    DATABASE_NAME = local.postgres.database_names[0]
    DATABASE_USER = module.db_connect_identity.name
  }

  db_setup_env_vars = merge(
    local.common_env,
    var.deploy_database_as_container ? local.container_db_env : local.vm_db_env
  )

  # --- Webapp environment ---
  web_base_env = {
    ALLOWED_HOSTS = "${local.name_prefix}-web.${var.default_domain}"
  }

  container_web_env = {
    DATABASE_HOST     = local.webapp_database.container_app_fqdn
    DATABASE_NAME     = "manage_breast_screening"
    DATABASE_USER     = "admin"
    DATABASE_PASSWORD = "secret"
  }

  vm_web_env = {
    DATABASE_HOST = local.postgres.host
    DATABASE_NAME = local.postgres.database_names[0]
    DATABASE_USER = module.db_connect_identity.name
  }

  webapp_env_vars = merge(
    local.common_env,
    local.web_base_env,
    var.deploy_database_as_container ? local.container_web_env : local.vm_web_env
  )
}

module "webapp" {

  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }
  source                           = "../dtos-devops-templates/infrastructure/modules/container-app"
  name                             = "${var.app_short_name}-web-${var.environment}"
  container_app_environment_id     = var.container_app_environment_id
  resource_group_name              = azurerm_resource_group.main.name
  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  infra_key_vault_name             = "kv-${var.app_short_name}-${var.env_config}-inf"
  infra_key_vault_rg               = "rg-${var.app_short_name}-${var.env_config}-infra"
  enable_auth                      = var.enable_auth
  app_key_vault_id                 = var.app_key_vault_id
  docker_image                     = var.docker_image
  user_assigned_identity_ids       = [module.db_connect_identity.id]
  environment_variables            = local.webapp_env_vars
  is_web_app                       = true
  port                             = 8000
}

resource "random_password" "admin_password" {
  count = var.deploy_database_as_container ? 1 : 0

  length           = 30
  special          = true
  override_special = "!@#$%^&*()-_=+[]{}<>:?"
}

resource "azurerm_key_vault_secret" "db_admin_pwd" {
  count = var.deploy_database_as_container ? 1 : 0

  name         = "${var.app_short_name}-db-${var.environment}-password"
  value        = resource.random_password.admin_password[0].result
  key_vault_id = var.app_key_vault_id
}

module "webapp_database" {
  count = var.deploy_database_as_container ? 1 : 0

  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }
  app_key_vault_id                 = var.app_key_vault_id
  source                           = "../dtos-devops-templates/infrastructure/modules/container-app"
  name                             = "${var.app_short_name}-db-${var.environment}"
  container_app_environment_id     = var.container_app_environment_id
  docker_image                     = "postgres:16"
  enable_auth                      = false
  environment_variables = {
    POSTGRES_PASSWORD         = "secret"
    POSTGRES_HOST_AUTH_METHOD = "trust"
    POSTGRES_USER             = "admin"
    POSTGRES_DB               = "manage_breast_screening"
  }
  resource_group_name              = azurerm_resource_group.main.name
  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  infra_key_vault_name             = "kv-${var.app_short_name}-${var.env_config}-inf"
  infra_key_vault_rg               = "rg-${var.app_short_name}-${var.env_config}-infra"
  is_tcp_app                       = true
  port = 5432
}
