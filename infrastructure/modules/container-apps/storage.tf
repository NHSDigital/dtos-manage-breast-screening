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
  log_analytics_workspace_id = var.log_analytics_workspace_id
  # log_analytics_workspace_id = module.log_analytics_workspace_audit.id

  monitor_diagnostic_setting_storage_account_enabled_logs = ["StorageWrite", "StorageRead", "StorageDelete"]
  monitor_diagnostic_setting_storage_account_metrics      = ["AllMetrics"]

  name = replace(lower(local.storage_account_name), "-", "")

  private_endpoint_properties = {
    private_dns_zone_ids_blob            = [data.azurerm_private_dns_zone.storage-account-blob.id]
    private_dns_zone_ids_queue           = [data.azurerm_private_dns_zone.storage-account-queue.id]
    private_endpoint_enabled             = true
    private_endpoint_subnet_id           = var.main_subnet_id
    private_endpoint_resource_group_name = azurerm_resource_group.main.name
    private_service_connection_is_manual = false
  }
  rbac_roles          = ["Storage Queue Data Contributor", "Storage Blob Data Contributor"]
  queues              = local.storage_queues
  resource_group_name = azurerm_resource_group.main.name
  action_group_id     = var.action_group_id
  enable_alerting     = var.enable_alerting
}
