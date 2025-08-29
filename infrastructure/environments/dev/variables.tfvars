dns_zone_name                         = "manage-breast-screening.non-live.screening.nhs.uk"
enable_auth                           = true
fetch_secrets_from_app_key_vault      = true
front_door_profile                    = "afd-nonlive-hub-manbrs"
postgres_backup_retention_days        = 7
postgres_geo_redundant_backup_enabled = false
protect_keyvault                      = false
vnet_address_space                    = "10.128.0.0/16"
personas_enabled                      = true
seed_demo_data                        = true
storage_account_name                  = "stmanbrsdevuks"

storage_containers = {
  notifications-mesh-data = {
    container_name        = "notifications-mesh-data"
    container_access_type = "private"
  }
  notifications-reports = {
    container_name        = "notifications-reports"
    container_access_type = "private"
  }
}

storage_queues = ["notifications-status-updates", "notifications-retry-message-batch"]
