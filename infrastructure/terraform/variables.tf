variable "deploy_infra" {
  description = "The foundational layer of infrastructure for the application to run on"
  type        = bool
  default     = true
}

variable "deploy_container_apps" {
  description = "Deploy the container app to the foundational infra"
  type        = bool
  default     = true
}

variable "app_short_name" {
  description = "Application short name (6 characters)"
  type        = string
}

variable "environment" {
  description = "Application environment name"
  type        = string
}

variable "env_config" {
  description = "Environment configuration. Different environments may share the same environment config and the same infrastructure"
  type        = string
}

variable "hub" {
  description = "Hub name (dev or prod)"
  type        = string
}

variable "docker_image" {
  description = "Docker image full path including registry, repository and tag"
  type        = string
}

variable "hub_subscription_id" {
  description = "ID of the hub Azure subscription"
  type        = string
}

variable "vnet_address_space" {
  description = "VNET address space. Must be unique across the hub."
  type        = string
}

variable "fetch_secrets_from_app_key_vault" {
  description = <<EOT
    Set to false initially to create and populate the app key vault.

    Then set to true to let the container app read secrets from the key vault."
    EOT
  default     = false
  type        = bool
}
variable "protect_keyvault" {
  description = "Ability to recover the key vault or its secrets after deletion"
  default     = true
  type        = bool
}

variable "postgres_backup_retention_days" {
  description = "The number of days to retain backups for the PostgreSQL Flexible Server."
  type        = number
  default     = 30
}

variable "postgres_geo_redundant_backup_enabled" {
  description = "Whether geo-redundant backup is enabled for the PostgreSQL Flexible Server."
  type        = bool
  default     = true
}

variable "postgres_prevent_destroy" {
  type        = bool
  default     = true
  description = "If true, prevents the PostgreSQL flexible server from being destroyed."
}

variable "postgres_sku_name" {
  description = "Value of the PostgreSQL Flexible Server SKU name"
  default     = "B_Standard_B1ms"
  type        = string
}
variable "postgres_storage_mb" {
  description = "Value of the PostgreSQL Flexible Server storage in MB"
  default     = 32768
  type        = number
}
variable "postgres_storage_tier" {
  description = "Value of the PostgreSQL Flexible Server storage tier"
  default     = "P4"
  type        = string
}

variable "enable_auth" {
  description = "Enable authentication for the container app. If true, the app will use Azure AD authentication."
  type        = bool
  default     = false
}

variable "use_apex_domain" {
  description = "Use apex domain for the Front Door endpoint. Set to true for production."
  type        = bool
  default     = false
}

variable "dns_zone_name" {
  description = "Value of the DNS zone name to use for the Front Door endpoint"
  type        = string
}

variable "front_door_profile" {
  description = "Name of the front door profile created for this application in the hub subscription"
  type        = string
}

variable "personas_enabled" {
  description = "To enable personas or not."
  type        = bool
  default     = false
}

locals {
  region = "uksouth"

  resource_group_name = "rg-${var.app_short_name}-${var.env_config}-uks"
}
