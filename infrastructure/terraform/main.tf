module "infra" {
  count = var.deploy_infra ? 1 : 0

  source = "../modules/infra"

  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }

  app_short_name                   = var.app_short_name
  environment                      = var.environment
  hub                              = var.hub
  docker_image                     = var.docker_image
  hub_subscription_id              = var.hub_subscription_id
  vnet_address_space               = var.vnet_address_space
  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  protect_keyvault                 = var.protect_keyvault
}

module "container-apps" {
  count = var.deploy_app ? 1 : 0

  source = "../modules/container-apps"

  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }

  app_short_name               = var.app_short_name
  environment                  = var.environment
  app_key_vault_id             = module.infra[0].app_key_vault_id
  container_app_environment_id = module.infra[0].container_app_environment_id

  hub                                   = var.hub
  docker_image                          = var.docker_image
  vnet_address_space                    = var.vnet_address_space
  fetch_secrets_from_app_key_vault      = var.fetch_secrets_from_app_key_vault
  postgres_backup_retention_days        = var.postgres_backup_retention_days
  postgres_geo_redundant_backup_enabled = var.postgres_geo_redundant_backup_enabled
  postgres_sku_name                     = var.postgres_sku_name
  postgres_storage_mb                   = var.postgres_storage_mb
  postgres_storage_tier                 = var.postgres_storage_tier
  enable_auth                           = var.enable_auth
  use_apex_domain                       = var.use_apex_domain
  vnet_name                             = module.infra[0].vnet_name
}
