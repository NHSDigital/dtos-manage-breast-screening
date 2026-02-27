data "azurerm_cdn_frontdoor_profile" "this" {
  provider = azurerm.hub

  name                = var.front_door_profile
  resource_group_name = "rg-hub-${var.hub}-uks-${var.app_short_name}"
}

resource "azurerm_cdn_frontdoor_firewall_policy" "this" {
  count    = 0 # temporarily disabled pending WAF smoke test investigation (DTOSS-12358)
  provider = azurerm.hub

  name                              = "wafmanbrs${replace(var.environment, "-", "")}"
  resource_group_name               = "rg-hub-${var.hub}-uks-${var.app_short_name}"
  sku_name                          = "Premium_AzureFrontDoor"
  mode                              = "Prevention"
  custom_block_response_status_code = 403

  managed_rule {
    type    = "Microsoft_DefaultRuleSet"
    version = "2.1"
    action  = "Block"
  }

  managed_rule {
    type    = "Microsoft_BotManagerRuleSet"
    version = "1.1"
    action  = "Block"
  }

  custom_rule {
    name     = "BlockNonUK"
    priority = 10
    type     = "MatchRule"
    action   = "Block"

    match_condition {
      match_variable     = "SocketAddr"
      operator           = "GeoMatch"
      negation_condition = true
      match_values       = ["GB"]
    }
  }

  custom_rule {
    name                           = "RateLimitPerIP"
    priority                       = 20
    type                           = "RateLimitRule"
    action                         = "Block"
    rate_limit_duration_in_minutes = 1
    rate_limit_threshold           = 300

    match_condition {
      match_variable     = "SocketAddr"
      operator           = "Any"
      negation_condition = false
      match_values       = []
    }
  }

  tags = {}
}

module "frontdoor_endpoint" {
  source = "../dtos-devops-templates/infrastructure/modules/cdn-frontdoor-endpoint"

  providers = {
    azurerm     = azurerm.hub # Each project's Front Door profile (with secrets) resides in Hub since it's shared infra with a Non-live/Live deployment pattern
    azurerm.dns = azurerm.hub
  }

  cdn_frontdoor_profile_id = data.azurerm_cdn_frontdoor_profile.this.id
  custom_domains = {
    "${var.environment}-domain" = {
      host_name        = local.hostname # For prod it must be equal to the dns_zone_name to use apex
      dns_zone_name    = var.dns_zone_name
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
        location               = var.region
        private_link_target_id = var.container_app_environment_id
      }
    }
  }
  route = {
    https_redirect_enabled = true
    supported_protocols    = ["Http", "Https"]
    patterns_to_match      = local.patterns_to_match
  }

  security_policies = {} # temporarily disabled pending WAF smoke test investigation (DTOSS-12358)
}
