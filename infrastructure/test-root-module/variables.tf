variable "name" {
  description = "Name of the Container App"
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group for both environment and app"
  type        = string
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "uksouth"
}

variable "environment_name" {
  description = "Name of the Container App Environment to create"
  type        = string
}

variable "log_analytics_name" {
  description = "Name for the Log Analytics Workspace"
  type        = string
}

variable "log_analytics_sku" {
  description = "SKU for Log Analytics (e.g. PerGB2018)"
  type        = string
  default     = "PerGB2018"
}

variable "log_analytics_retention" {
  description = "Retention in days for Log Analytics"
  type        = number
  default     = 30
}

variable "revision_mode" {
  description = "Revision mode (Single or Multiple)"
  type        = string
  default     = "Single"
}

variable "ingress_enabled" {
  description = "Enable external ingress"
  type        = bool
  default     = true
}

variable "allow_insecure_connections" {
  description = "Allow HTTP (insecure) traffic"
  type        = bool
  default     = false
}

variable "target_port" {
  description = "Port that the container listens on"
  type        = number
  default     = 80
}

variable "container_name" {
  description = "Name of the container inside the app"
  type        = string
  default     = "app"
}

variable "image" {
  description = "Container image to deploy"
  type        = string
}

variable "cpu" {
  description = "CPU cores for the container"
  type        = number
  default     = 0.5
}

variable "memory" {
  description = "Memory for the container (e.g. '1Gi')"
  type        = string
  default     = "0.5Gi"
}


# variable "client_secret_name" {
#   description = "Name of the secret in Container App to store AAD client secret"
#   type        = string
#   # default     = "aad-client-secret"
# }

# Always fetch the AAD client secret from Key Vault
variable "infra_key_vault_name" {
  description = "Name of Key Vault to retrieve the AAD client secret"
  type        = string
}

variable "infra_key_vault_rg" {
  description = "Resource group of the Key Vault"
  type        = string
}

# variable "key-vault-secret-client-secret" {
#   description = "Secret name in Key Vault for the AAD client secret"
#   type        = string
# }
# variable "key-vault-secret-client-id" {
#   description = "Secret name in Key Vault for the AAD client ID"
#   type        = string
# }

# variable "key-vault-secret-client-audiences" {
#   description = "Secret name in Key Vault for the AAD client audiences"
#   type        = string
# }

variable "fetch_secrets_from_infra_key_vault" {
  description = "Whether to fetch secrets from the infrastructure Key Vault"
  type        = bool
  default     = true

}

variable "enable_auth" {
  description = "Whether to configure AAD authentication on this Container App"
  type        = bool
  default     = true
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

variable "allowed_audiences" {
  description = "List of allowed audiences (client IDs or App ID URIs)"
  type        = list(string)
  default     = []
}
