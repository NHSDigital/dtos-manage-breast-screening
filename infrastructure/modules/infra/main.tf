resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.region
}

module "shared_config" {
  source = "../dtos-devops-templates/infrastructure/modules/shared-config"

  env         = var.environment
  location    = var.region
  application = var.app_short_name
}

module "hub_config" {
  source = "../dtos-devops-templates/infrastructure/modules/shared-config"

  env         = var.hub
  location    = var.region
  application = "hub"
}

module "app-key-vault" {
  source = "../dtos-devops-templates/infrastructure/modules/key-vault"

  name                                             = "kv-${var.app_short_name}-${var.environment}-app"
  resource_group_name                              = azurerm_resource_group.main.name
  enable_rbac_authorization                        = true
  location                                         = var.region
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
  source = "../dtos-devops-templates/infrastructure/modules/log-analytics-workspace"

  name     = module.shared_config.names.log-analytics-workspace
  location = var.region

  law_sku        = "PerGB2018"
  retention_days = 30

  monitor_diagnostic_setting_log_analytics_workspace_enabled_logs = ["SummaryLogs", "Audit"]
  monitor_diagnostic_setting_log_analytics_workspace_metrics      = ["AllMetrics"]

  resource_group_name = azurerm_resource_group.main.name
}

module "container-app-environment" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-environment"
  providers = {
    azurerm     = azurerm
    azurerm.dns = azurerm.hub
  }

  name                       = module.shared_config.names.container-app-environment
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = module.log_analytics_workspace_audit.id
  vnet_integration_subnet_id = module.container_app_subnet.id
  private_dns_zone_rg_name   = "rg-hub-${var.hub}-uks-private-dns-zones"
  zone_redundancy_enabled    = var.cae_zone_redundancy_enabled
}

module "app_insights_audit" {
  source = "../dtos-devops-templates/infrastructure/modules/app-insights"

  name                = module.shared_config.names.app-insights
  location            = var.region
  resource_group_name = azurerm_resource_group.main.name
  appinsights_type    = "web"

  log_analytics_workspace_id = module.log_analytics_workspace_audit.id

  enable_alerting = var.enable_alerting
}

module "private_link_scoped_service_law" {
  source = "../dtos-devops-templates/infrastructure/modules/private-link-scoped-service"

  providers = {
    azurerm = azurerm.hub
  }

  name                = "pls-${var.app_short_name}-${var.environment}-law"
  resource_group_name = "rg-hub-${var.hub}-uks-hub-private-endpoints"
  linked_resource_id  = module.log_analytics_workspace_audit.id
  scope_name          = "ampls-${var.hub}hub"
}

module "private_link_scoped_service_app_insights" {
  source = "../dtos-devops-templates/infrastructure/modules/private-link-scoped-service"

  providers = {
    azurerm = azurerm.hub
  }

  name                = "pls-${var.app_short_name}-${var.environment}-appinsights"
  resource_group_name = "rg-hub-${var.hub}-uks-hub-private-endpoints"
  linked_resource_id  = module.app_insights_audit.id
  scope_name          = "ampls-${var.hub}hub"
}
