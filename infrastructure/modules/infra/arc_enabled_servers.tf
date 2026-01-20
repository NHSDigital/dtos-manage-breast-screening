resource "azurerm_resource_group" "arc_enabled_servers" {
  count = var.enable_arc_servers ? 1 : 0

  name     = "${var.resource_group_name}-arc-enabled-servers"
  location = var.region
}

# Assign "Azure Connected Machine Onboarding" role to the service principal on Arc RG
resource "azurerm_role_assignment" "arc_onboarding_role" {
  count = var.enable_arc_servers ? 1 : 0

  scope                = azurerm_resource_group.arc_enabled_servers[0].id
  role_definition_name = "Azure Connected Machine Onboarding"
  principal_id         = data.azuread_service_principal.arc_onboarding[0].object_id
}


resource "azurerm_resource_group" "arc_automation" {
  count = var.enable_arc_servers ? 1 : 0

  name     = "${var.resource_group_name}-arc-automation"
  location = var.region
}
