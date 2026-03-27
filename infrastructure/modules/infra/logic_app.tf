resource "azurerm_logic_app_workflow" "slack_alert_transformer" {
  count               = var.enable_alerting ? 1 : 0
  name                = "logic-${var.app_short_name}-${var.environment}-slack-alerts"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region

  workflow_parameters = {
    "slackWebhookUrl" = jsonencode({
      type         = "SecureString"
      defaultValue = ""
    })
  }

  parameters = {
    "slackWebhookUrl" = data.azurerm_key_vault_secret.slack_webhook_url[0].value
  }
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
              alertRule        = { type = "string" }
              severity         = { type = "string" }
              firedDateTime    = { type = "string" }
              resolvedDateTime = { type = "string" }
              portalLink       = { type = "string" }
              monitorCondition = { type = "string" }
              description      = { type = "string" }
              configurationItems = {
                type  = "array"
                items = { type = "string" }
              }
            }
          }
        }
      }
    }
  })
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
        "uri": "@parameters('slackWebhookUrl')",
        "headers": {
          "Content-Type": "application/json"
        },
        "body": {
          "blocks": [
            {
              "type": "header",
              "text": {
                "type": "plain_text",
                "text": "@{if(equals(triggerBody()?['data']?['essentials']?['monitorCondition'], 'Resolved'), concat('✅ Resolved – ', triggerBody()?['data']?['essentials']?['alertRule']), concat('🚨 Alert – ', triggerBody()?['data']?['essentials']?['alertRule']))}",
                "emoji": true
              }
            },
            {
              "type": "section",
              "fields": [
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Severity*\n', triggerBody()?['data']?['essentials']?['severity'])}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Status*\n', triggerBody()?['data']?['essentials']?['monitorCondition'])}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Fired At*\n', triggerBody()?['data']?['essentials']?['firedDateTime'])}"
                },
                {
                  "type": "mrkdwn",
                  "text": "@{concat('*Resource*\n`', coalesce(triggerBody()?['data']?['essentials']?['configurationItems']?[0], 'N/A'), '`')}"
                }
              ]
            },
            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "@{concat('*Description*\n> ', coalesce(triggerBody()?['data']?['essentials']?['description'], 'N/A'))}"
              }
            },
            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "@{concat(':mag: <https://portal.azure.com/#resource', triggerBody()?['data']?['essentials']?['alertTargetIDs']?[0], '/failures|View Failures in App Insights>')}"
              }
            }
          ]
        }
      },
      "runAfter": {}
    }
  BODY

  depends_on = [azurerm_logic_app_trigger_http_request.azure_monitor_alert]
}
