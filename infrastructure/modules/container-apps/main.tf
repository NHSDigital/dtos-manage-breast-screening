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

# create the database
# prod  : make migrate seed [default]
# dev   : make migrate seed [default]
# review: make migrate seed example_data
# put "example_data" once the PR has been merged in.
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

  environment_variables = local.webapp_db_setup_vars
}

locals {
  base_webapp_env_vars = {
    ALLOWED_HOSTS   = "${var.app_short_name}-web-${var.environment}.${var.default_domain}"
    DATABASE_HOST   = module.postgres.host
    DATABASE_NAME   = module.postgres.database_names[0]
    DATABASE_USER   = module.db_connect_identity.name
    SSL_MODE        = "require"
    AZURE_CLIENT_ID = module.db_connect_identity.client_id
  }

  webapp_env_vars = var.env_config == "review" ? merge(
    local.base_webapp_env_vars,
    {
      DATABASE_HOST             = module.webapp_database.container_app_fqdn
      DATABASE_NAME             = "manage_breast_screening"
      DATABASE_USER             = "admin"
      AZURE_CLIENT_ID           = ""
      DATABASE_PASSWORD         = "secret"
    }
  ) : local.base_webapp_env_vars

  base_db_setup_vars = {
    DATABASE_HOST    = module.postgres.host
    DATABASE_NAME    = module.postgres.database_names[0]
    DATABASE_USER    = module.db_connect_identity.name
    SSL_MODE         = "require"
    AZURE_CLIENT_ID  = module.db_connect_identity.client_id
    PERSONAS_ENABLED = var.personas_enabled ? "1" : "0"
    DJANGO_ENV       = var.env_config
  }

  webapp_db_setup_vars = var.env_config == "review" ? merge(
    local.base_db_setup_vars,
    {
      DATABASE_HOST             = module.webapp_database.container_app_fqdn
      DATABASE_NAME             = "manage_breast_screening"
      DATABASE_USER             = "admin"
    }
  ) : local.base_db_setup_vars
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


module "webapp_database" {
  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }
  source                           = "../dtos-devops-templates/infrastructure/modules/container-app"
  name                             = "${var.app_short_name}-db-${var.environment}"
  container_app_environment_id     = var.container_app_environment_id
  resource_group_name              = azurerm_resource_group.main.name
  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  infra_key_vault_name             = "kv-${var.app_short_name}-${var.env_config}-inf"
  infra_key_vault_rg               = "rg-${var.app_short_name}-${var.env_config}-infra"
  enable_auth                      = false
  app_key_vault_id                 = var.app_key_vault_id
  docker_image                     = "postgres:16"
  is_tcp_app                       = true
  environment_variables            =  {
    POSTGRES_PASSWORD         = "secret"
    POSTGRES_HOST_AUTH_METHOD = "trust"
    POSTGRES_USER             = "admin"
    POSTGRES_DB               = "manage_breast_screening"
  }
  port                        = 5432
}
