api_oauth_token_url                   = "https://int.api.service.nhs.uk/oauth2/token"
dns_zone_name                         = "manage-breast-screening.non-live.screening.nhs.uk"
enable_auth                           = false
fetch_secrets_from_app_key_vault      = true
front_door_profile                    = "afd-nonlive-hub-manbrs"
postgres_backup_retention_days        = 7
postgres_geo_redundant_backup_enabled = false
protect_keyvault                      = false
vnet_address_space                    = "10.128.0.0/16"
seed_demo_data                        = true
nhs_notify_api_message_batch_url      = "https://int.api.service.nhs.uk/comms/v1/message-batches"

monitor_action_group = {
  action_group_1 = {
    short_name = "group1"
    email_receiver = {
      alert_team = {
        name                    = "email1"
        email_address           = "alert_team@testing.com"
        use_common_alert_schema = false
      }
    }
  }
}
