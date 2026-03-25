data "azurerm_subscription" "current" {}

data "azurerm_key_vault" "infra" {
  provider = azurerm.hub

  name                = var.infra_key_vault_name
  resource_group_name = var.infra_key_vault_rg
}
