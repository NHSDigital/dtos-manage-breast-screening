data "azurerm_private_dns_zone" "relay" {
  count    = var.enable_arc_servers ? 1 : 0
  provider = azurerm.hub

  name                = "privatelink.servicebus.windows.net"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}

module "relay_namespace" {
  count  = var.enable_arc_servers ? 1 : 0
  source = "../dtos-devops-templates/infrastructure/modules/relay-namespace"

  name                = "relay-${var.app_short_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region

  log_analytics_workspace_id                    = module.log_analytics_workspace_audit.id
  monitor_diagnostic_setting_relay_enabled_logs = ["HybridConnectionsEvent"]
  monitor_diagnostic_setting_relay_metrics      = ["AllMetrics"]

  private_endpoint_properties = {
    private_endpoint_enabled             = true
    private_endpoint_subnet_id           = module.main_subnet.id
    private_endpoint_resource_group_name = azurerm_resource_group.main.name
    private_dns_zone_ids_relay           = [data.azurerm_private_dns_zone.relay[0].id]
  }
}
