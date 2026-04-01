module "monitor_action_group" {
  source = "../dtos-devops-templates/infrastructure/modules/monitor-action-group"

  name                = "${module.shared_config.names.monitor-action-group}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  short_name          = "ag-${var.environment}"

  webhook_receiver = var.enable_alerting ? {
    slack = {
      name                    = "slack-alert-transformer"
      service_uri             = module.logic_app_slack_alert[0].trigger_callback_url
      use_common_alert_schema = true
    }
  } : null
}
