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

  container_args = [
    var.seed_demo_data
    ? "python manage.py migrate && python manage.py seed_demo_data --noinput"
    : "python manage.py migrate"
  ]
  secret_variables           = var.deploy_database_as_container ? { DATABASE_PASSWORD = resource.random_password.admin_password[0].result } : {}
  docker_image               = var.docker_image
  user_assigned_identity_ids = var.deploy_database_as_container ? [] : [module.db_connect_identity[0].id]
  environment_variables = merge(
    local.common_env,
    var.deploy_database_as_container ? local.container_db_env : local.azure_db_env
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
  user_assigned_identity_ids       = var.deploy_database_as_container ? [] : [module.db_connect_identity[0].id]
  environment_variables = merge(
    local.common_env,
    {
      ALLOWED_HOSTS = "${var.app_short_name}-web-${var.environment}.${var.default_domain}"
    },
    var.deploy_database_as_container ? local.container_db_env : local.azure_db_env
  )
  secret_variables = var.deploy_database_as_container ? { DATABASE_PASSWORD = resource.random_password.admin_password[0].result } : {}
  is_web_app       = true
  port             = 8000
}
