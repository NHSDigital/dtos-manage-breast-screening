data "azurerm_client_config" "current" {}

data "azurerm_key_vault" "infra" {
  count    = var.enable_alerting ? 1 : 0
  provider = azurerm.hub

  name                = var.infra_key_vault_name
  resource_group_name = var.infra_key_vault_rg
}

data "azurerm_key_vault_secret" "slack_webhook_url" {
  count        = var.enable_alerting ? 1 : 0
  provider     = azurerm.hub
  name         = "slack-webhook-url"
  key_vault_id = data.azurerm_key_vault.infra[0].id
}

data "azurerm_application_insights" "app_insights" {
  count               = var.enable_alerting ? 1 : 0
  name                = split("/", var.app_insights_id)[8]
  resource_group_name = split("/", var.app_insights_id)[4]
}

data "azurerm_subscription" "current" {}

data "azuread_group" "postgres_sql_admin_group" {
  display_name = var.postgres_sql_admin_group
}

data "azurerm_private_dns_zone" "storage" {
  provider = azurerm.hub

  name                = "privatelink.blob.core.windows.net"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}

data "azurerm_private_dns_zone" "storage-account-blob" {
  provider = azurerm.hub

  name                = "privatelink.blob.core.windows.net"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}

data "azurerm_private_dns_zone" "storage-account-queue" {
  provider = azurerm.hub

  name                = "privatelink.queue.core.windows.net"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}
