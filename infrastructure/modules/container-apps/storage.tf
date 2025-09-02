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

  name                = local.storage_account_name
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  containers          = var.storage_containers
  queues              = var.storage_queues
}
