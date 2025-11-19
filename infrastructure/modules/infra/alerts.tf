module "service_health_alert" {
  source = "../dtos-devops-templates/infrastructure/modules/monitor-activity-log-alert"

  name                = "service-health-alerts-${var.app_short_name}-${var.environment}"
  location            = "global"
  resource_group_name = azurerm_resource_group.main.name
  description         = "Azure Service Health alert for services impacting ${var.app_short_name} in ${var.environment}"

  scopes = [data.azurerm_subscription.current.id]

  criteria = {
    category = "ServiceHealth"
    level    = null

    service_health = {
      events    = ["Incident", "Maintenance", "Informational", "ActionRequired", "Security"]
      locations = [var.region]

      # Only monitor Azure services used by this application
      # This reduces noise from unrelated service health events
      services = [
        "Application Insights",
        "Azure Container Apps",
        "Azure Container Service",
        "Azure Container Storage",
        "Azure Database for PostgreSQL flexible servers",
        "Azure DNS",
        "Azure Frontdoor",
        "Azure Monitor",
        "Azure Private Link",
        "Key Vault",
        "Log Analytics",
        "Storage",
        "Virtual Network",
        "Windows Virtual Desktop"
      ]
    }
  }

  action_group_id = module.monitor_action_group.monitor_action_group.id
}
