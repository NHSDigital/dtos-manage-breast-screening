variable "app_key_vault_id" {
  description = "Application key vault ID"
  type        = string
}

variable "app_short_name" {
  description = "Application short name (6 characters)"
  type        = string
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

variable "enable_auth" {
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

variable "log_analytics_workspace_audit_id" {
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

variable "personas_enabled" {
  description = "To enable personas or not."
  type        = bool
  default     = false
}

variable "seed_demo_data" {
  description = "Whether or not to seed the demo data in the database."
  type        = bool
  default     = false
}

variable "use_apex_domain" {
  description = "Use apex domain for the Front Door endpoint. Set to true for production."
  type        = bool
}

locals {
  resource_group_name = "rg-${var.app_short_name}-${var.environment}-container-app-uks"

  hostname = var.use_apex_domain ? var.dns_zone_name : "${var.environment}.${var.dns_zone_name}"

  database_user = "admin"
  database_name = "manage_breast_screening"

  common_env = {
    SSL_MODE         = "require"
    PERSONAS_ENABLED = var.personas_enabled ? "1" : "0"
    DJANGO_ENV       = var.env_config
  }

  container_db_env = {
    DATABASE_HOST = var.deploy_database_as_container ? module.database_container[0].container_app_fqdn : null
    DATABASE_NAME = local.database_name
    DATABASE_USER = local.database_user
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
  }
  storage_queues = ["notifications-message-status-updates", "notifications-message-batch-retries"]
}
