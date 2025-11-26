variable "app_short_name" {
  description = "Application short name (6 characters)"
  type        = string
}

variable "environment" {
  description = "Application environment name"
  type        = string
}

variable "resource_group_name" {
  description = "Infra resource group name"
  type        = string
}

variable "hub" {
  description = "Hub name (dev or prod)"
  type        = string
}

variable "region" {
  description = "The region to deploy in"
  type        = string
}

variable "vnet_address_space" {
  description = "VNET address space. Must be unique across the hub."
  type        = string
}

variable "protect_keyvault" {
  description = "Ability to recover the key vault or its secrets after deletion"
  type        = bool
}

variable "infra_key_vault_name" {
  description = "Name of the infra key vault"
  type        = string
}

variable "infra_key_vault_rg" {
  description = "Name of the infra key vault resource group"
  type        = string
}

variable "cae_zone_redundancy_enabled" {
  description = "Specifies whether the Container App Environment should be zone redundant."
  type        = bool
}

variable "enable_alerting" {
  description = "Whether monitoring and alerting is enabled."
  type        = bool
}

locals {
  hub_vnet_rg_name = "rg-hub-${var.hub}-uks-hub-networking"
}
