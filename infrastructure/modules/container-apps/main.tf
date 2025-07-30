resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = local.region
}

module "db_migrate" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-dbm-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name
  container_command            = ["python"]
  container_args               = ["manage.py", "migrate"]
  docker_image                 = var.docker_image
  user_assigned_identity_ids   = [module.db_connect_identity.id]
  environment_variables = {
    DATABASE_HOST   = module.postgres.host
    DATABASE_NAME   = module.postgres.database_names[0]
    DATABASE_USER   = module.db_connect_identity.name
    SSL_MODE        = "require"
    AZURE_CLIENT_ID = module.db_connect_identity.client_id
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
  infra_key_vault_name             = "kv-manbrs-${var.environment}-infra"
  infra_key_vault_rg               = "rg-manbrs-${var.environment}-infra"
  enable_auth                      = var.enable_auth
  app_key_vault_id                 = var.app_key_vault_id
  docker_image                     = var.docker_image
  user_assigned_identity_ids       = [module.db_connect_identity.id]
  environment_variables = {
    ALLOWED_HOSTS   = "manage-breast-screening-web-${var.environment}.${module.container-app-environment.default_domain}"
    DATABASE_HOST   = module.postgres.host
    DATABASE_NAME   = module.postgres.database_names[0]
    DATABASE_USER   = module.db_connect_identity.name
    SSL_MODE        = "require"
    AZURE_CLIENT_ID = module.db_connect_identity.client_id
  }
  is_web_app = true
  http_port  = 8000
}
