data "azurerm_private_dns_zone" "storage" {
  provider = azurerm.hub

  name                = "privatelink.blob.core.windows.net"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}

module "azure_blob_storage_identity" {
  source              = "../dtos-devops-templates/infrastructure/modules/managed-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  uai_name            = "mi-${var.app_short_name}-${var.environment}-blob-storage"
}

module "azure_queue_storage_identity" {
  source              = "../dtos-devops-templates/infrastructure/modules/managed-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  uai_name            = "mi-${var.app_short_name}-${var.environment}-queue-storage"
}

module "storage" {
  source = "../dtos-devops-templates/infrastructure/modules/storage"

  containers                 = local.storage_containers
  location                   = var.region
  log_analytics_workspace_id = var.log_analytics_workspace_audit_id
  # log_analytics_workspace_id = module.log_analytics_workspace_audit.id

  monitor_diagnostic_setting_storage_account_enabled_logs = ["StorageWrite", "StorageRead", "StorageDelete"]
  monitor_diagnostic_setting_storage_account_metrics      = ["AllMetrics"]

  name = replace(lower(local.storage_account_name), "-", "")

  private_endpoint_properties = {
    private_endpoint_enabled             = true
    private_endpoint_subnet_id           = var.main_subnet_id
    private_endpoint_resource_group_name = azurerm_resource_group.main.name
    private_service_connection_is_manual = false
  }
  queues              = local.storage_queues
  resource_group_name = azurerm_resource_group.main.name
}

module "blob_storage_role_assignment" {
  source               = "../dtos-devops-templates/infrastructure/modules/rbac-assignment"
  principal_id         = module.azure_blob_storage_identity.principal_id
  role_definition_name = "Storage Blob Data Contributor"
  scope                = module.storage.storage_account_id
  depends_on           = [module.storage]
}

module "queue_storage_role_assignment" {
  source               = "../dtos-devops-templates/infrastructure/modules/rbac-assignment"
  principal_id         = module.azure_queue_storage_identity.principal_id
  role_definition_name = "Storage Queue Data Contributor"
  scope                = module.storage.storage_account_id
  depends_on           = [module.storage]
}
