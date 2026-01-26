module "relay_hybrid_connection" {
  count  = var.relay_namespace_name != null ? 1 : 0
  source = "../dtos-devops-templates/infrastructure/modules/relay-hybrid-connection"

  name                 = "hc-${var.app_short_name}-${var.environment}"
  relay_namespace_name = var.relay_namespace_name
  resource_group_name  = var.resource_group_name_infra

  authorization_rules = {
    "${var.app_short_name}-${var.environment}-listen-send" = {
      listen = true
      send   = true
    }
  }
}
