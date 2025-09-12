output "app_key_vault_id" {
  value = module.app-key-vault.key_vault_id
}

output "container_app_environment_id" {
  value = module.container-app-environment.id
}

output "vnet_name" {
  value = module.main_vnet.name
}

output "log_analytics_workspace_audit_id" {
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
