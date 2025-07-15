resource "azurerm_container_app_environment" "env" {
  name                               = var.environment_name
  location                           = var.location
  resource_group_name                = var.resource_group_name
  infrastructure_resource_group_name = "${var.resource_group_name}-cae-infra"
  # log_analytics_workspace_id         = azurerm_log_analytics_workspace.la.id

  workload_profile {
    maximum_count         = 3
    minimum_count         = 1
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }
}

# create a Container App with optional AAD authentication
resource "azurerm_container_app" "this" {
  name                         = var.name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = var.revision_mode

  ingress {
    external_enabled           = var.ingress_enabled
    allow_insecure_connections = var.allow_insecure_connections
    target_port                = var.target_port
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    container {
      name   = var.container_name
      image  = var.image
      cpu    = var.cpu
      memory = var.memory
    }
  }
