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
  default     = true
}

variable "monitor_action_group" {
  description = "Default configuration for the monitor action groups."
  type = map(object({
    short_name = string
    email_receiver = optional(map(object({
      name                    = string
      email_address           = string
      use_common_alert_schema = optional(bool, false)
    })))
    event_hub_receiver = optional(map(object({
      name                    = string
      event_hub_namespace     = string
      event_hub_name          = string
      subscription_id         = string
      use_common_alert_schema = optional(bool, false)
    })))
    sms_receiver = optional(map(object({
      name         = string
      country_code = string
      phone_number = string
    })))
    voice_receiver = optional(map(object({
      name         = string
      country_code = string
      phone_number = string
    })))
    webhook_receiver = optional(map(object({
      name                    = string
      service_uri             = string
      use_common_alert_schema = optional(bool, false)
    })))
  }))
}

locals {
  hub_vnet_rg_name = "rg-hub-${var.hub}-uks-hub-networking"
}
