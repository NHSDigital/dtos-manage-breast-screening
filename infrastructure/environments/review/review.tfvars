features = {
  is_functional_infra = false
  is_container_apps   = true
}

vnet_address_space                    = "10.141.0.0/16"
fetch_secrets_from_app_key_vault      = true
protect_keyvault                      = false
postgres_backup_retention_days        = 7
postgres_geo_redundant_backup_enabled = false
