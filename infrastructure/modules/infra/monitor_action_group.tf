module "monitor_action_group" {
  for_each = local.monitor_action_group_map

  source = "../dtos-devops-templates/infrastructure/modules/monitor-action-group"

  name                = module.shared_config.names.monitor-action-group
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  short_name          = each.value.short_name
  email_receiver      = each.value.email_receiver
  event_hub_receiver  = each.value.event_hub_receiver
  sms_receiver        = each.value.sms_receiver
  voice_receiver      = each.value.voice_receiver
  webhook_receiver    = each.value.webhook_receiver
}

locals {
  monitor_action_group_map = {
    for action_group_key, action_group_details in var.monitor_action_group :
    action_group_key => merge(
      {
        action_group_key = action_group_key
      },
      action_group_details
    )
  }
}
