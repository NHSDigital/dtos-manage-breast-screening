data "azurerm_private_dns_zone" "servicebus" {
  count    = var.enable_service_bus ? 1 : 0
  provider = azurerm.hub

  name                = "privatelink.servicebus.windows.net"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}

module "servicebus_namespace" {
  count  = var.enable_service_bus ? 1 : 0
  source = "../dtos-devops-templates/infrastructure/modules/service-bus"

  servicebus_namespace_name = "sbns-${var.app_short_name}-${var.environment}-uks"
  resource_group_name       = azurerm_resource_group.main.name
  location                  = var.region

  sku_tier                       = "Premium"
  capacity                       = 1
  servicebus_topic_map           = var.servicebus_topics

  private_endpoint_properties = {
    private_endpoint_enabled             = true
    private_endpoint_subnet_id           = module.main_subnet.id
    private_endpoint_resource_group_name = azurerm_resource_group.main.name
    private_dns_zone_ids                 = [data.azurerm_private_dns_zone.servicebus[0].id]
  }
}
