data "azurerm_client_config" "current" {}

data "azuread_group" "postgres_sql_admin_group" {
  display_name = var.postgres_sql_admin_group
}
