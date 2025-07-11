variable "app_short_name" {
  description = "Application short name (6 characters)"
}

variable "environment" {
  description = "Application environment name"
}

variable "hub" {
  description = "Hub name (dev or prod)"
}

variable "docker_image" {
  description = "Docker image full path including registry, repository and tag"
}

variable "hub_subscription_id" {
  description = "ID of the hub Azure subscription"
}

variable "vnet_address_space" {
  description = "VNET address space. Must be unique across the hub."
}

variable "fetch_secrets_from_app_key_vault" {
  description = <<EOT
    Set to false initially to create and populate the app key vault.

    Then set to true to let the container app read secrets from the key vault."
    EOT
  default     = false
}

variable "fetch_secrets_from_infra_key_vault" {
  description = <<EOT
    Fetch secrets from the infra key vault to be used to setup the identity provider. Requires app_key_vault_id.

    WARNING: The key vault must be created by terraform and populated manually before setting this to true.
    EOT
  type        = bool
  default     = false
  nullable    = false
}

variable "protect_keyvault" {
  description = "Ability to recover the key vault or its secrets after deletion"
  default     = true
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

variable "postgres_sku_name" {
  default = "B_Standard_B1ms"
}
variable "postgres_storage_mb" {
  default = 32768
}
variable "postgres_storage_tier" {
  default = "P4"
}

variable "enable_auth" {
  description = "Enable authentication for the container app. If true, the app will use Azure AD authentication."
  type        = bool
  default     = false
}

variable "unauthenticated_action" {
  description = "Action for unauthenticated requests: RedirectToLoginPage, Return401, Return403, AllowAnonymous"
  type        = string
  default     = "RedirectToLoginPage"
  validation {
    condition     = contains(["RedirectToLoginPage", "Return401", "Return403", "AllowAnonymous"], var.unauthenticated_action)
    error_message = "Invalid unauthenticated action. Must be one of: RedirectToLoginPage, Return401, Return403, AllowAnonymous."
  }
}

# Always fetch the AAD client secret from Key Vault
variable "infra_key_vault_name" {
  description = "Name of Key Vault to retrieve the AAD client secrets"
  type        = string
}

variable "infra_key_vault_rg" {
  description = "Resource group of the Key Vault"
  type        = string
}


locals {
  region              = "uksouth"
  resource_group_name = "rg-${var.app_short_name}-${var.environment}-uks"
  hub_vnet_rg_name    = "rg-hub-${var.hub}-uks-hub-networking"

  postgres_sql_admin_group = "postgres_manbrs_${var.environment}_uks_admin"
}
