module "monitor_action_group" {
  source = "../dtos-devops-templates/infrastructure/modules/monitor-action-group"

  name                = module.shared_config.names.monitor-action-group
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  short_name          = module.shared_config.names.monitor-action-group
  email_receiver      =  {
    name            = "email"
    email_address   = var.monitoring_email_address
  }
}
