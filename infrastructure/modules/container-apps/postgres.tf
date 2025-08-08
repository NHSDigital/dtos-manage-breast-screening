data "azurerm_private_dns_zone" "postgres" {
  provider = azurerm.hub

  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}

module "postgres" {
  source = "../dtos-devops-templates/infrastructure/modules/postgresql-flexible"

  # postgresql Server
  name                = module.shared_config.names.postgres-sql-server
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region

  backup_retention_days           = var.postgres_backup_retention_days
  geo_redundant_backup_enabled    = var.postgres_geo_redundant_backup_enabled
  postgresql_admin_object_id      = data.azuread_group.postgres_sql_admin_group.object_id
  postgresql_admin_principal_name = var.postgres_sql_admin_group
  postgresql_admin_principal_type = "Group"
  administrator_login             = "admin"
  admin_identities                = [module.db_connect_identity]

  # Diagnostic Settings
  log_analytics_workspace_id                                = var.log_analytics_workspace_audit_id
  monitor_diagnostic_setting_postgresql_server_enabled_logs = ["PostgreSQLLogs", "PostgreSQLFlexSessions", "PostgreSQLFlexQueryStoreRuntime", "PostgreSQLFlexQueryStoreWaitStats", "PostgreSQLFlexTableStats", "PostgreSQLFlexDatabaseXacts"]
  monitor_diagnostic_setting_postgresql_server_metrics      = ["AllMetrics"]

  sku_name     = var.postgres_sku_name
  storage_mb   = var.postgres_storage_mb
  storage_tier = var.postgres_storage_tier

  server_version = "16"
  tenant_id      = data.azurerm_client_config.current.tenant_id

  # Private Endpoint Configuration if enabled
  private_endpoint_properties = {
    private_dns_zone_ids_postgresql      = [data.azurerm_private_dns_zone.postgres.id]
    private_endpoint_enabled             = true
    private_endpoint_subnet_id           = var.postgres_subnet_id
    private_endpoint_resource_group_name = azurerm_resource_group.main.name
    private_service_connection_is_manual = false
  }

  databases = {
    db1 = {
      collation   = "en_US.utf8"
      charset     = "UTF8"
      max_size_gb = 10
      name        = "manage_breast_screening"
    }
  }

  tags = {}
}

module "db_connect_identity" {
  source              = "../dtos-devops-templates/infrastructure/modules/managed-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  uai_name            = "mi-${var.app_short_name}-${var.environment}-db-connect"
}
