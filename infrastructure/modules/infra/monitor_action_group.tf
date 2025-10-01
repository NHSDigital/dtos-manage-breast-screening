module "monitor_action_group" {
  source = "../dtos-devops-templates/infrastructure/modules/monitor-action-group"

  name                = module.shared_config.names.monitor-action-group
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  short_name          = "ag-${var.environment}"
  email_receiver = {
    email = {
      name          = "email"
      email_address = data.azurerm_key_vault_secret.infra.value
    }
  }
}
