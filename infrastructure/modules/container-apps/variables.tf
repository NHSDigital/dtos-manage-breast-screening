variable "api_oauth_token_url" {
  description = "The OAuth API endpoint URL used to request client credentials for NHS Notify API"
  type        = string
  default     = null
}

variable "app_key_vault_id" {
  description = "Application key vault ID"
  type        = string
}

variable "app_short_name" {
  description = "Application short name (6 characters)"
  type        = string
}

variable "resource_group_name_infra" {
  description = "resource group name infra"
  type        = string
}

variable "allowed_paths" {
  description = "List of allowed paths for manbrs service. Empty = allow all."
  type        = list(string)
}

variable "container_app_environment_id" {
  description = "The ID of the container app environment where container apps are deployed"
  type        = string
}

variable "default_domain" {
  description = "The container app environment default domain"
  type        = string
}

variable "dns_zone_name" {
  description = "Public DNS zone name"
  type        = string
}

variable "docker_image" {
  description = "Docker image full path including registry, repository and tag"
  type        = string
}

variable "enable_entra_id_authentication" {
  description = "Enable authentication for the container app. If true, the app will use Azure AD authentication."
  type        = bool
}

variable "env_config" {
  description = "Environment configuration. Different environments may share the same environment config and the same infrastructure"
  type        = string
}

variable "environment" {
  description = "Application environment name"
  type        = string
}

variable "fetch_secrets_from_app_key_vault" {
  description = <<EOT
    Set to false initially to create and populate the app key vault.

    Then set to true to let the container app read secrets from the key vault."
    EOT
  type        = bool
}

variable "front_door_profile" {
  description = "Name of the front door profile created for this application in the hub subscription"
  type        = string
}

variable "hub" {
  description = "Hub name (dev or prod)"
  type        = string
}

variable "log_analytics_workspace_id" {
  description = "Log analytics workspace audit ID"
  type        = string
}


variable "deploy_database_as_container" {
  description = "Whether to deploy the database as a container or as an Azure postgres flexible server."
  type        = bool
}

variable "nhs_notify_api_message_batch_url" {
  description = "The API endpoint URL used to send message batches to NHS Notify"
  type        = string
  default     = null
}

variable "postgres_backup_retention_days" {
  description = "The number of days to retain backups for the PostgreSQL Flexible Server."
  type        = number
}

variable "postgres_geo_redundant_backup_enabled" {
  description = "Whether geo-redundant backup is enabled for the PostgreSQL Flexible Server."
  type        = bool
}

variable "postgres_sku_name" {
  description = "Value of the PostgreSQL Flexible Server SKU name"
  type        = string
}

variable "postgres_sql_admin_group" {
  description = "Entra ID group which is granted admin access to the PostgreSQL Flexible Server."
  type        = string
}

variable "postgres_storage_mb" {
  description = "Value of the PostgreSQL Flexible Server storage in MB"
  type        = number
}

variable "postgres_storage_tier" {
  description = "Value of the PostgreSQL Flexible Server storage tier"
  type        = string
}

variable "postgres_subnet_id" {
  description = "The postgres subnet id. Created in the infra module."
  type        = string
}

variable "main_subnet_id" {
  description = "The main subnet id. Created in the infra module."
  type        = string
}

variable "region" {
  description = "The region to deploy in"
  type        = string
}

variable "seed_demo_data" {
  description = "Whether or not to seed the demo data in the database."
  type        = bool
}

variable "use_apex_domain" {
  description = "Use apex domain for the Front Door endpoint. Set to true for production."
  type        = bool
}

variable "enable_alerting" {
  description = "Whether monitoring and alerting is enabled for the PostgreSQL Flexible Server."
  type        = bool
}

variable "target_url" {
  description = "The external url"
  type        = string
}

variable "alert_window_size" {
  type     = string
  nullable = false
  validation {
    condition     = contains(["PT1M", "PT5M", "PT15M", "PT30M", "PT1H", "PT6H", "PT12H"], var.alert_window_size)
    error_message = "The alert_window_size must be one of: PT1M, PT5M, PT15M, PT30M, PT1H, PT6H, PT12H"
  }
  description = "The period of time that is used to monitor alert activity e.g. PT1M, PT5M, PT15M, PT30M, PT1H, PT6H, PT12H. The interval between checks is adjusted accordingly."
}

variable "action_group_id" {
  type        = string
  description = "ID of the action group to notify."
}

variable "infra_key_vault_name" {
  description = "Name of the infra key vault"
  type        = string
}

variable "infra_key_vault_rg" {
  description = "Name of the infra key vault resource group"
  type        = string
}

variable "app_insights_connection_string" {
  description = "The Application Insights connection string."
  type        = string
}

variable "app_insights_id" {
  description = "The Application Insights id."
  type        = string
}

variable "queue_length_alert_threshold" {
  description = "If alerting is enabled, alert if storage account queues are greater than this threshold."
  type        = number
}

variable "enable_notifications_jobs_schedule" {
  description = "Whether we apply the cron schedules for the notifications container app jobs"
  type        = bool
  default     = false
}

locals {
  resource_group_name = "rg-${var.app_short_name}-${var.environment}-container-app-uks"

  hostname = var.use_apex_domain ? var.dns_zone_name : "${var.environment}.${var.dns_zone_name}"

  database_user = "admin"
  database_name = "manage_breast_screening"
  # Here we expect the environment to be in format pr-XXX. For example PR 1234 would have environment pr-1234 and port 2234
  database_port = var.deploy_database_as_container ? try(tonumber(regex("\\d+", var.environment)), 24) + 1000 : 5432
  env_vars_from_yaml = yamldecode(
    file("${path.module}/../../environments/${var.env_config}/variables.yml")
  )
  common_env = merge(
    local.env_vars_from_yaml,
    {
      SSL_MODE   = "require"
      DJANGO_ENV = var.env_config
    }
  )
  container_db_env = {
    DATABASE_HOST = var.deploy_database_as_container ? module.database_container[0].container_app_fqdn : null
    DATABASE_NAME = local.database_name
    DATABASE_USER = local.database_user
    DATABASE_PORT = local.database_port
  }

  azure_db_env = {
    AZURE_CLIENT_ID = var.deploy_database_as_container ? null : module.db_connect_identity[0].client_id
    DATABASE_HOST   = var.deploy_database_as_container ? null : module.postgres[0].host
    DATABASE_NAME   = var.deploy_database_as_container ? null : module.postgres[0].database_names[0]
    DATABASE_USER   = var.deploy_database_as_container ? null : module.db_connect_identity[0].name
  }

  storage_account_name = "st${var.app_short_name}${var.environment}uks"
  storage_containers = {
    notifications-mesh-data = {
      container_name        = "notifications-mesh-data"
      container_access_type = "private"
    }
    notifications-reports = {
      container_name        = "notifications-reports"
      container_access_type = "private"
    }
    notifications-smoke-test-reports = {
      container_name        = "notifications-smoke-test-reports"
      container_access_type = "private"
    }
  }
  storage_queues = ["notifications-message-status-updates", "notifications-message-batch-retries"]

  always_allowed_paths = ["/sha", "/healthcheck"]
  # If allowed_paths is not set, use the module default which allows any pattern
  # If it is set, include the default paths
  patterns_to_match = (var.allowed_paths == null ? null :
    concat(local.always_allowed_paths, var.allowed_paths)
  )
}
