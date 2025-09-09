data "azurerm_client_config" "current" {}

data "azuread_group" "postgres_sql_admin_group" {
  display_name = var.postgres_sql_admin_group
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
