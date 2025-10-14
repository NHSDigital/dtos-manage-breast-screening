module "infra" {
  count = var.deploy_infra ? 1 : 0

  source = "../modules/infra"

  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }

  region               = local.region
  resource_group_name  = local.resource_group_name
  infra_key_vault_name = local.infra_key_vault_name
  infra_key_vault_rg   = local.infra_key_vault_rg
  app_short_name       = var.app_short_name
  environment          = var.env_config
  hub                  = var.hub
  protect_keyvault     = var.protect_keyvault
  vnet_address_space   = var.vnet_address_space
}

module "shared_config" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/shared-config"

  env         = var.env_config
  location    = local.region
  application = var.app_short_name
}

module "container-apps" {
  count = var.deploy_container_apps ? 1 : 0

  source = "../modules/container-apps"

  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }

  region                                = local.region
  action_group_id                       = var.deploy_infra ? module.infra[0].monitor_action_group_id : data.azurerm_monitor_action_group.main[0].id
  alert_window_size                     = var.alert_window_size
  enable_alerting                       = var.enable_alerting
  app_key_vault_id                      = var.deploy_infra ? module.infra[0].app_key_vault_id : data.azurerm_key_vault.app_key_vault[0].id
  app_short_name                        = var.app_short_name
  app_insights_connection_string        = var.deploy_infra ? module.infra[0].app_insights_connection_string : data.azurerm_application_insights.app_insights[0].connection_string
  allowed_paths                         = var.allowed_paths
  container_app_environment_id          = var.deploy_infra ? module.infra[0].container_app_environment_id : data.azurerm_container_app_environment.this[0].id
  default_domain                        = var.deploy_infra ? module.infra[0].default_domain : data.azurerm_container_app_environment.this[0].default_domain
  dns_zone_name                         = var.dns_zone_name
  docker_image                          = var.docker_image
  deploy_database_as_container          = var.deploy_database_as_container
  enable_entra_id_authentication        = var.enable_entra_id_authentication
  environment                           = var.environment
  env_config                            = var.env_config
  fetch_secrets_from_app_key_vault      = var.fetch_secrets_from_app_key_vault
  front_door_profile                    = var.front_door_profile
  hub                                   = var.hub
  log_analytics_workspace_id            = var.deploy_infra ? module.infra[0].log_analytics_workspace_id : data.azurerm_log_analytics_workspace.audit[0].id
  postgres_backup_retention_days        = var.postgres_backup_retention_days
  postgres_geo_redundant_backup_enabled = var.postgres_geo_redundant_backup_enabled
  postgres_sku_name                     = var.postgres_sku_name
  postgres_sql_admin_group              = "postgres_${var.app_short_name}_${var.env_config}_uks_admin"
  postgres_storage_mb                   = var.postgres_storage_mb
  postgres_storage_tier                 = var.postgres_storage_tier
  postgres_subnet_id                    = var.deploy_infra ? module.infra[0].postgres_subnet_id : data.azurerm_subnet.postgres[0].id
  main_subnet_id                        = var.deploy_infra ? module.infra[0].main_subnet_id : data.azurerm_subnet.main[0].id
  seed_demo_data                        = var.seed_demo_data
  use_apex_domain                       = var.use_apex_domain
  infra_key_vault_name                  = local.infra_key_vault_name
  infra_key_vault_rg                    = local.infra_key_vault_rg
  api_oauth_token_url                   = var.api_oauth_token_url
  nhs_notify_api_message_batch_url      = var.nhs_notify_api_message_batch_url
}
