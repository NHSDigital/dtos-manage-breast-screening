data "azurerm_private_dns_zone" "postgres" {
  provider = azurerm.hub

  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = "rg-hub-${var.hub}-uks-private-dns-zones"
}

# Don't deploy if deploy_database_as_container is true
module "postgres" {
  count = var.deploy_database_as_container ? 0 : 1

  source = "../dtos-devops-templates/infrastructure/modules/postgresql-flexible"

  # postgresql Server
  name                = module.shared_config.names.postgres-sql-server
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region

  backup_retention_days           = var.postgres_backup_retention_days
  geo_redundant_backup_enabled    = var.postgres_geo_redundant_backup_enabled
  enable_high_availability        = var.postgres_enable_high_availability
  postgresql_admin_object_id      = data.azuread_group.postgres_sql_admin_group.object_id
  postgresql_admin_principal_name = var.postgres_sql_admin_group
  postgresql_admin_principal_type = "Group"
  administrator_login             = local.database_user
  admin_identities                = [module.db_connect_identity[0]]

  # Diagnostic Settings
  log_analytics_workspace_id                                = var.log_analytics_workspace_id
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

  # alerts
  action_group_id         = var.action_group_id
  enable_alerting         = var.enable_alerting
  alert_memory_threshold  = 60
  alert_cpu_threshold     = 90
  alert_storage_threshold = 60

  databases = {
    db1 = {
      collation   = "en_US.utf8"
      charset     = "UTF8"
      max_size_gb = 10
      name        = local.database_name
    }
  }

  tags = {}
}

module "db_connect_identity" {
  count = var.deploy_database_as_container ? 0 : 1

  source              = "../dtos-devops-templates/infrastructure/modules/managed-identity"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region
  uai_name            = "mi-${var.app_short_name}-${var.environment}-db-connect"
}

resource "random_password" "admin_password" {
  count = var.deploy_database_as_container ? 1 : 0

  length           = 30
  special          = true
  override_special = "!@#$%^&*()-_=+"
}

module "database_container" {
  count = var.deploy_database_as_container ? 1 : 0

  providers = {
    azurerm     = azurerm
    azurerm.hub = azurerm.hub
  }
  source                       = "../dtos-devops-templates/infrastructure/modules/container-app"
  name                         = "${var.app_short_name}-db-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  docker_image                 = "postgres:16"
  secret_variables             = var.deploy_database_as_container ? { POSTGRES_PASSWORD = resource.random_password.admin_password[0].result } : {}
  environment_variables = {
    POSTGRES_USER = local.database_user
    POSTGRES_DB   = local.database_name
  }

  # alerts
  action_group_id        = var.action_group_id
  enable_alerting        = var.enable_alerting
  alert_memory_threshold = 60
  alert_cpu_threshold    = 90

  resource_group_name = azurerm_resource_group.main.name
  is_tcp_app          = true
  # postgres has a port of 5432
  port         = 5432
  exposed_port = local.database_port
}
