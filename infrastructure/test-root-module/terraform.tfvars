
# Basic Container App settings
name                = "my-app"
resource_group_name = "container-app-rg"
location            = "uksouth"

# Container App Environment & logging
environment_name        = "my-app-env"
# log_analytics_name      = "la-production"
# log_analytics_sku       = "PerGB2018"
# log_analytics_retention = 30

# Container image + sizing
image          = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
container_name = "web"
cpu            = 0.5
memory         = "1.0Gi"

# Ingress & revision
revision_mode              = "Single"
ingress_enabled            = true
allow_insecure_connections = false
target_port                = 80
