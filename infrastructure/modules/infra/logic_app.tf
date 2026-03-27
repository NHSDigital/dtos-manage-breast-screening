module "logic_app_slack_alert" {
  count  = var.enable_alerting ? 1 : 0
  source = "../dtos-devops-templates/infrastructure/modules/logic-app-slack-alert"

  name                = "logic-${var.app_short_name}-${var.environment}-slack-alerts"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  slack_webhook_url   = data.azurerm_key_vault_secret.slack_webhook_url[0].value
}
