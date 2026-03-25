module "monitor_action_group" {
  source = "../dtos-devops-templates/infrastructure/modules/monitor-action-group"

  name                = "${module.shared_config.names.monitor-action-group}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  short_name          = "ag-${var.environment}"

  webhook_receiver = var.enable_alerting ? {
    slack = {
      name                    = "slack-alert-transformer"
      service_uri             = azurerm_logic_app_trigger_http_request.azure_monitor_alert[0].callback_url
      use_common_alert_schema = true
    }
  } : null
}
