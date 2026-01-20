data "azurerm_subscription" "current" {}

data "azurerm_key_vault" "infra" {
  provider = azurerm.hub

  name                = var.infra_key_vault_name
  resource_group_name = var.infra_key_vault_rg
}

data "azurerm_key_vault_secret" "infra" {
  name         = "monitoring-email-address"
  key_vault_id = data.azurerm_key_vault.infra.id
}

data "azuread_service_principal" "arc_onboarding" {
  count = var.enable_arc_servers ? 1 : 0

  display_name = "spn-azure-arc-onboarding-screening-${var.environment}"
}
