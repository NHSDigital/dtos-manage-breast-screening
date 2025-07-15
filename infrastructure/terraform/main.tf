resource "azurerm_resource_group" "main" {
  name     = local.resource_group_name
  location = local.region
}

module "shared_config" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/shared-config"

  env         = var.environment
  location    = local.region
  application = var.app_short_name
}

module "hub_config" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/shared-config"

  env         = var.hub
  location    = local.region
  application = "hub"
}

module "app-key-vault" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/key-vault"

  name                                             = "kv-${var.app_short_name}-${var.environment}-app"
  resource_group_name                              = azurerm_resource_group.main.name
  enable_rbac_authorization                        = true
  location                                         = local.region
  log_analytics_workspace_id                       = module.log_analytics_workspace_audit.id
  monitor_diagnostic_setting_keyvault_enabled_logs = ["AuditEvent", "AzurePolicyEvaluationDetails"]
  monitor_diagnostic_setting_keyvault_metrics      = ["AllMetrics"]
  private_endpoint_properties = {
    private_dns_zone_ids_keyvault        = [data.azurerm_private_dns_zone.key-vault.id]
    private_endpoint_enabled             = true
    private_endpoint_subnet_id           = module.main_subnet.id
    private_endpoint_resource_group_name = azurerm_resource_group.main.name
    private_service_connection_is_manual = false
  }
  purge_protection_enabled = var.protect_keyvault
}

module "log_analytics_workspace_audit" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/log-analytics-workspace"

  name     = module.shared_config.names.log-analytics-workspace
  location = local.region

  law_sku        = "PerGB2018"
  retention_days = 30

  monitor_diagnostic_setting_log_analytics_workspace_enabled_logs = ["SummaryLogs", "Audit"]
  monitor_diagnostic_setting_log_analytics_workspace_metrics      = ["AllMetrics"]

  resource_group_name = azurerm_resource_group.main.name
}

module "container-app-environment" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/container-app-environment"
  providers = {
    azurerm     = azurerm
    azurerm.dns = azurerm.hub
  }

  name                       = "manage-breast-screening-${var.environment}"
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = module.log_analytics_workspace_audit.id
  vnet_integration_subnet_id = module.container_app_subnet.id
  private_dns_zone_rg_name   = "rg-hub-${var.hub}-uks-private-dns-zones"
}

module "db_migrate" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "manage-breast-screening-dbm-${var.environment}"
  container_app_environment_id = module.container-app-environment.id
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

resource "terraform_data" "job_image" {
  input = module.db_migrate.image
}

resource "azapi_resource_action" "start_db_migration" {
  resource_id = module.db_migrate.id
  type        = "Microsoft.App/jobs@2024-03-01"
  action      = "start"
  body        = {}

  lifecycle {
    replace_triggered_by = [terraform_data.job_image]
  }
}

module "webapp" {
  source                           = "../modules/dtos-devops-templates/infrastructure/modules/container-app"
  name                             = "manage-breast-screening-web-${var.environment}"
  container_app_environment_id     = module.container-app-environment.id
  resource_group_name              = azurerm_resource_group.main.name
  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = module.app-key-vault.key_vault_id
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
