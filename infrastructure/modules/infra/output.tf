output "app_key_vault_id" {
  value = module.app-key-vault.key_vault_id
}

output "container_app_environment_id" {
  value = module.container-app-environment.id
}

output "vnet_name" {
  value = module.main_vnet.name
}

output "log_analytics_workspace_id" {
  value = module.log_analytics_workspace_audit.id
}

output "default_domain" {
  value = module.container-app-environment.default_domain
}

output "postgres_subnet_id" {
  value = module.postgres_subnet.id
}

output "main_subnet_id" {
  value = module.main_subnet.id
}

output "monitor_action_group_id" {
  value = module.monitor_action_group.monitor_action_group.id
}

output "app_insights_connection_string" {
  value = module.app_insights_audit.connection_string
}

output "app_insights_id" {
  value = module.app_insights_audit.id
}

output "relay_namespace_name" {
  value = var.enable_arc_servers ? module.relay_namespace[0].name : null
}

output "servicebus_namespace_name" {
  value = var.enable_service_bus ? module.servicebus_namespace[0].namespace_name : null
}

output "servicebus_namespace_id" {
  value = var.enable_service_bus ? module.servicebus_namespace[0].namespace_id : null
}

output "servicebus_topic_ids" {
  value = var.enable_service_bus ? module.servicebus_namespace[0].topic_ids : {}
}
