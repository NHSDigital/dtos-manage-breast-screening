# data "azurerm_private_dns_zone" "postgres" {
#   provider = azurerm.hub

#   name                = "privatelink.postgres.database.azure.com"
#   resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
# }

# module "postgres_subnet" {
#   source = "../dtos-devops-templates/infrastructure/modules/subnet"

#   name                                                           = "snet-postgres"
#   resource_group_name                                            = azurerm_resource_group.main.name
#   vnet_name                                                      = module.main_vnet.name
#   address_prefixes                                               = [cidrsubnet(var.vnet_address_space, 7, 1)]
#   create_nsg                                                     = false
#   location                                                       = "UK South"
#   monitor_diagnostic_setting_network_security_group_enabled_logs = []
#   log_analytics_workspace_id                                     = module.log_analytics_workspace_audit.id
#   network_security_group_name                                    = "nsg-postgres"
# }

# module "postgres" {
#   source = "../dtos-devops-templates/infrastructure/modules/postgresql-flexible"

#   # postgresql Server
#   name                = module.shared_config.names.postgres-sql-server
#   resource_group_name = azurerm_resource_group.main.name
#   location            = local.region

#   backup_retention_days           = var.postgres_backup_retention_days
#   geo_redundant_backup_enabled    = var.postgres_geo_redundant_backup_enabled
#   postgresql_admin_object_id      = data.azuread_group.postgres_sql_admin_group.object_id
#   postgresql_admin_principal_name = local.postgres_sql_admin_group
#   postgresql_admin_principal_type = "Group"
#   administrator_login             = "admin"
#   admin_identities                = [module.db_connect_identity]

#   # Diagnostic Settings
#   log_analytics_workspace_id                                = module.log_analytics_workspace_audit.id
#   monitor_diagnostic_setting_postgresql_server_enabled_logs = ["PostgreSQLLogs", "PostgreSQLFlexSessions", "PostgreSQLFlexQueryStoreRuntime", "PostgreSQLFlexQueryStoreWaitStats", "PostgreSQLFlexTableStats", "PostgreSQLFlexDatabaseXacts"]
#   monitor_diagnostic_setting_postgresql_server_metrics      = ["AllMetrics"]

#   sku_name     = var.postgres_sku_name
#   storage_mb   = var.postgres_storage_mb
#   storage_tier = var.postgres_storage_tier

#   server_version = "16"
#   tenant_id      = data.azurerm_client_config.current.tenant_id

#   # Private Endpoint Configuration if enabled
#   private_endpoint_properties = {
#     private_dns_zone_ids_postgresql      = [data.azurerm_private_dns_zone.postgres.id]
#     private_endpoint_enabled             = true
#     private_endpoint_subnet_id           = module.postgres_subnet.id
#     private_endpoint_resource_group_name = azurerm_resource_group.main.name
#     private_service_connection_is_manual = false
#   }

#   databases = {
#     db1 = {
#       collation   = "en_US.utf8"
#       charset     = "UTF8"
#       max_size_gb = 10
#       name        = "manage_breast_screening"
#     }
#   }

#   depends_on = [
#     module.peering_spoke_hub,
#     module.peering_hub_spoke
#   ]

#   tags = {}
# }

# module "db_connect_identity" {
#   source              = "../dtos-devops-templates/infrastructure/modules/managed-identity"
#   resource_group_name = local.resource_group_name
#   location            = local.region
#   uai_name            = "mi-${var.app_short_name}-${var.environment}-db-connect"
# }
