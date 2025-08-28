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

variable "region" {
  description = "The region to deploy in"
  type        = string
}

variable "personas_enabled" {
  description = "To enable personas or not."
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
}
