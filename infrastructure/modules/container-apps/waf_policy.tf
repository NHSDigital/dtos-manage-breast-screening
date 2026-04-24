resource "azurerm_cdn_frontdoor_firewall_policy" "this" {
  count    = var.deploy_infra ? 1 : 0
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

    override {
      rule_group_name = "General"
      rule {
        rule_id = "200002"
        enabled = true
        action  = "Log"
      }
      rule {
        rule_id = "200003"
        enabled = true
        action  = "Log"
      }
    }

    override {
      rule_group_name = "RFI"
      rule {
        rule_id = "931130"
        enabled = true
        action  = "Log"
      }
    }
  }

  managed_rule {
    type    = "Microsoft_BotManagerRuleSet"
    version = "1.1"
    action  = "Block"
  }

  custom_rule {
    name                           = "RateLimitPerIP"
    priority                       = 20
    type                           = "RateLimitRule"
    action                         = "Block"
    rate_limit_duration_in_minutes = 1
    rate_limit_threshold           = 1000

    match_condition {
      match_variable     = "SocketAddr"
      operator           = "Any"
      negation_condition = false
      match_values       = []
    }
  }

  tags = {}
}
