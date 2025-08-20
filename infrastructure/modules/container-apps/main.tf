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

  environment_variables = {
    DATABASE_HOST    = module.postgres.host
    DATABASE_NAME    = module.postgres.database_names[0]
    DATABASE_USER    = module.db_connect_identity.name
    SSL_MODE         = "require"
    AZURE_CLIENT_ID  = module.db_connect_identity.client_id
    PERSONAS_ENABLED = var.personas_enabled ? "1" : "0"
    DJANGO_ENV       = var.env_config
  }
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
  environment_variables = {
    ALLOWED_HOSTS   = "${var.app_short_name}-web-${var.environment}.${var.default_domain}"
    DATABASE_HOST   = module.postgres.host
    DATABASE_NAME   = module.postgres.database_names[0]
    DATABASE_USER   = module.db_connect_identity.name
    SSL_MODE        = "require"
    AZURE_CLIENT_ID = module.db_connect_identity.client_id
  }
  is_web_app = true
  http_port  = 8000
}
