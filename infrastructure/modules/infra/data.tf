data "azurerm_subscription" "current" {}

data "azurerm_key_vault" "infra" {
  provider = azurerm.hub

  name                = var.infra_key_vault_name
  resource_group_name = var.infra_key_vault_rg
}

data "azurerm_key_vault_secret" "slack_webhook_url" {
  count        = var.enable_alerting ? 1 : 0
  name         = "slack-webhook-url"
  key_vault_id = data.azurerm_key_vault.infra.id
}
