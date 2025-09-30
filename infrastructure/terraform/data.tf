# Only do these looks ups if we have already deployed the infra code in a previous run, else don't use it
data "azurerm_container_app_environment" "this" {
  count = var.deploy_infra ? 0 : 1

  name                = module.shared_config.names.container-app-environment
  resource_group_name = local.resource_group_name
}

data "azurerm_key_vault" "app_key_vault" {
  count = var.deploy_infra ? 0 : 1

  name                = "kv-${var.app_short_name}-${var.env_config}-app"
  resource_group_name = local.resource_group_name
}

data "azurerm_log_analytics_workspace" "audit" {
  count = var.deploy_infra ? 0 : 1

  name                = module.shared_config.names.log-analytics-workspace
  resource_group_name = local.resource_group_name
}

data "azurerm_subnet" "postgres" {
  count = var.deploy_infra ? 0 : 1

  name                 = "snet-postgres"
  virtual_network_name = module.shared_config.names.virtual-network-lowercase
  resource_group_name  = local.resource_group_name
}

data "azurerm_subnet" "main" {
  count = var.deploy_infra ? 0 : 1

  name                 = "snet-main"
  virtual_network_name = module.shared_config.names.virtual-network-lowercase
  resource_group_name  = local.resource_group_name
}

data "azurerm_monitor_action_group" "main" {
  count = var.deploy_infra ? 0 : 1

  name                = module.shared_config.names.monitor-action-group
  resource_group_name = local.resource_group_name
}
