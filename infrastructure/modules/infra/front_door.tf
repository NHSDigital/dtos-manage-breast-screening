data "azurerm_cdn_frontdoor_profile" "this" {
  provider = azurerm.hub

  name                = "afd-${local.hub_live_name}-hub-manbrs"
  resource_group_name = "rg-hub-${var.hub}-uks-manbrs"
}

module "frontdoor_endpoint" {
  source = "../modules/dtos-devops-templates/infrastructure/modules/cdn-frontdoor-endpoint"

  providers = {
    azurerm     = azurerm.hub # Each project's Front Door profile (with secrets) resides in Hub since it's shared infra with a Non-live/Live deployment pattern
    azurerm.dns = azurerm.hub
  }

  cdn_frontdoor_profile_id = data.azurerm_cdn_frontdoor_profile.this.id
  custom_domains = {
    "${var.environment}-domain" = {
      host_name        = local.hostname # For prod it must be equal to the dns_zone_name to use apex
      dns_zone_name    = local.dns_zone_name
      dns_zone_rg_name = "rg-hub-${var.hub}-uks-public-dns-zones"
    }
  }
  name = var.environment # environment-specific to avoid naming collisions within a Front Door Profile

  origins = {
    "${var.environment}-origin" = {
      hostname           = module.webapp.fqdn
      origin_host_header = module.webapp.fqdn
      private_link = {
        target_type            = "managedEnvironments"
        location               = local.region
        private_link_target_id = module.container-app-environment.id
      }
    }
  }
}
