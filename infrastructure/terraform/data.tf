# Only do these looks ups if we have already deployed the infra code in a previous run, else don't use it
data "azurerm_container_app_environment" "this" {
  count               = var.deploy_container_app ? 1 : 0

  name                = "${var.app_short_name}-${var.env_config}"
  resource_group_name = local.resource_group_name
}

data "azurerm_key_vault" "app_key_vault" {
  count               = var.deploy_container_app ? 1 : 0

  name                = "kv-${var.app_short_name}-${var.env_config}-app"
  resource_group_name = local.resource_group_name
}

data "azurerm_log_analytics_workspace" "audit" {
  count               = var.deploy_container_app ? 1 : 0

  name                = module.shared_config.names.log-analytics-workspace
  resource_group_name = local.resource_group_name
}
