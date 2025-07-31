output "app_key_vault_id" {
  value = module.app-key-vault.key_vault_id
}

output "container_app_environment_id" {
  value = module.container-app-environment.id
}

output "vnet_name" {
  value = module.main_vnet.name
}


output  log_analytics_workspace_audit {
  value = module.log_analytics_workspace_audit.id
}
