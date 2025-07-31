data "azurerm_container_app_environment" "this" {
  name                = "${var.app_short_name}-${var.backend_id}"
  resource_group_name = local.resource_group_name
}

data "azurerm_key_vault" "app_key_vault" {
  name                = "kv-${var.app_short_name}-${var.backend_id}-app"
  resource_group_name = local.resource_group_name
}

data "azurerm_log_analytics_workspace" "audit" {
  name                = module.shared_config.names.log-analytics-workspace
  resource_group_name = local.resource_group_name
}
