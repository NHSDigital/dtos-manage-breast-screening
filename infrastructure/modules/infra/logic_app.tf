resource "azurerm_logic_app_workflow" "slack_alert_transformer" {
  count               = var.enable_alerting ? 1 : 0
  name                = "logic-${var.app_short_name}-${var.environment}-slack-alerts"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_role_assignment" "logic_app_kv_secrets_user" {
  count    = var.enable_alerting ? 1 : 0
  provider = azurerm.hub

  scope                = "${data.azurerm_key_vault.infra.id}/secrets/slack-webhook-url"
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_logic_app_workflow.slack_alert_transformer[0].identity[0].principal_id
}

resource "azurerm_role_assignment" "logic_app_app_insights_monitoring_reader" {
  count = var.enable_alerting ? 1 : 0

  scope                = module.app_insights_audit.id
  role_definition_name = "Monitoring Reader"
  principal_id         = azurerm_logic_app_workflow.slack_alert_transformer[0].identity[0].principal_id
}

resource "azurerm_logic_app_trigger_http_request" "azure_monitor_alert" {
  count        = var.enable_alerting ? 1 : 0
  name         = "When_an_HTTP_request_is_received"
  logic_app_id = azurerm_logic_app_workflow.slack_alert_transformer[0].id
  method       = "POST"

  schema = jsonencode({
    "$schema" = "http://json-schema.org/draft-04/schema#"
    type      = "object"
    properties = {
      schemaId = { type = "string" }
      data = {
        type = "object"
        properties = {
          essentials = {
            type = "object"
            properties = {
              alertRuleName      = { type = "string" }
              severity           = { type = "string" }
              firedDateTime      = { type = "string" }
              resolvedDateTime   = { type = "string" }
              portalLink         = { type = "string" }
              monitorCondition   = { type = "string" }
              targetResourceName = { type = "string" }
              description        = { type = "string" }
            }
          }
          alertContext = {
            type = "object"
            properties = {
              condition = {
                type = "object"
                properties = {
                  allOf = {
                    type  = "array"
                    items = {
                      type = "object"
                      properties = {
                        linkToSearchResultsUI = { type = "string" }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  })
}

resource "azurerm_logic_app_action_custom" "get_slack_webhook_url" {
  count        = var.enable_alerting ? 1 : 0
  name         = "Get_Slack_Webhook_URL"
  logic_app_id = azurerm_logic_app_workflow.slack_alert_transformer[0].id

  body = <<-BODY
    {
      "type": "Http",
      "inputs": {
        "method": "GET",
        "uri": "https://${var.infra_key_vault_name}.vault.azure.net/secrets/slack-webhook-url/?api-version=7.4",
        "authentication": {
          "type": "ManagedServiceIdentity",
          "audience": "https://vault.azure.net"
        }
      },
      "runAfter": {}
    }
  BODY

  depends_on = [azurerm_logic_app_trigger_http_request.azure_monitor_alert]
}

resource "azurerm_logic_app_action_custom" "query_app_insights" {
  count        = var.enable_alerting ? 1 : 0
  name         = "Query_App_Insights"
  logic_app_id = azurerm_logic_app_workflow.slack_alert_transformer[0].id

  body = <<-BODY
    {
      "type": "Http",
      "inputs": {
        "method": "POST",
        "uri": "https://api.applicationinsights.io/v1/apps/${module.app_insights_audit.app_id}/query",
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "query": "exceptions | where timestamp > ago(10m) | project type, outerMessage, url = tostring(customDimensions['url']), operation_Id | order by timestamp desc | take 1"
        },
        "authentication": {
          "type": "ManagedServiceIdentity",
          "audience": "https://api.applicationinsights.io"
        }
      },
      "runAfter": {}
    }
  BODY

  depends_on = [azurerm_logic_app_trigger_http_request.azure_monitor_alert]
}

resource "azurerm_logic_app_action_custom" "post_to_slack" {
  count        = var.enable_alerting ? 1 : 0
  name         = "Post_to_Slack"
  logic_app_id = azurerm_logic_app_workflow.slack_alert_transformer[0].id

  body = <<-BODY
    {
      "type": "Http",
      "inputs": {
        "method": "POST",
        "uri": "@body('Get_Slack_Webhook_URL')?['value']",
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "blocks": [
            {
              "type": "header",
              "text": {
                "type": "plain_text",
                "text": "@{if(equals(triggerBody()?['data']?['essentials']?['monitorCondition'], 'Resolved'), concat('✅ Resolved – ', triggerBody()?['data']?['essentials']?['alertRuleName']), concat('🚨 Exception – ', triggerBody()?['data']?['essentials']?['alertRuleName']))}",
                "emoji": true
              }
            },
            {
              "type": "section",
              "fields": [
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Environment*\n`', triggerBody()?['data']?['essentials']?['targetResourceName'], '`')}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Severity*\n', triggerBody()?['data']?['essentials']?['severity'])}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Fired At*\n', triggerBody()?['data']?['essentials']?['firedDateTime'])}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Status*\n', triggerBody()?['data']?['essentials']?['monitorCondition'])}"
                }
              ]
            },
            {
              "type": "divider"
            },
            {
              "type": "section",
              "fields": [
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Exception Type*\n`', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[0], 'N/A'), '`')}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Affected URL*\n`', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[2], 'N/A'), '`')}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Message*\n', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[1], 'N/A'))}"
                }
              ]
            },
            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "@{concat(':azure: <', triggerBody()?['data']?['essentials']?['portalLink'], '|View Alert>    :mag: <', triggerBody()?['data']?['alertContext']?['condition']?['allOf']?[0]?['linkToSearchResultsUI'], '|View in App Insights>')}"
              }
            }
          ]
        }
      },
      "runAfter": {
        "Get_Slack_Webhook_URL": ["Succeeded"],
        "Query_App_Insights": ["Succeeded", "Failed", "Skipped", "TimedOut"]
      }
    }
  BODY

  depends_on = [
    azurerm_logic_app_action_custom.get_slack_webhook_url,
    azurerm_logic_app_action_custom.query_app_insights
  ]
}
