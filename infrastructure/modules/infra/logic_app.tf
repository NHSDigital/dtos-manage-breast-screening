resource "azurerm_logic_app_workflow" "slack_alert_transformer" {
  count               = var.enable_alerting ? 1 : 0
  name                = "logic-${var.app_short_name}-${var.environment}-slack-alerts"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.region

  identity {
    type = "SystemAssigned"
  }

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
                        metricName            = { type = "string" }
                        metricValue           = { type = "number" }
                        threshold             = { type = "number" }
                        operator              = { type = "string" }
                        timeAggregation       = { type = "string" }
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

resource "azurerm_logic_app_action_custom" "route_alert" {
  count        = var.enable_alerting ? 1 : 0
  name         = "Route_Alert"
  logic_app_id = azurerm_logic_app_workflow.slack_alert_transformer[0].id

  body = <<-BODY
    {
      "type": "If",
      "expression": {
        "and": [
          {
            "contains": [
              "@triggerBody()?['data']?['essentials']?['alertRule']",
              "exceptions-alert"
            ]
          }
        ]
      },
      "actions": {
        "Query_App_Insights": {
          "type": "Http",
          "inputs": {
            "method": "POST",
            "uri": "https://api.applicationinsights.io/v1/apps/${module.app_insights_audit.app_id}/query",
            "headers": {
              "Content-Type": "application/json"
            },
            "body": {
              "query": "exceptions | where timestamp between (datetime_add('minute', -15, todatetime('@{triggerBody()?['data']?['essentials']?['firedDateTime']}')) .. todatetime('@{triggerBody()?['data']?['essentials']?['firedDateTime']}')) | summarize Count=count(), ExceptionType=any(type), Message=substring(any(outerMessage), 0, 300), Url=any(tostring(customDimensions['url'])), OperationId=any(operation_Id), RoleName=any(cloud_RoleName), FirstSeen=format_datetime(min(timestamp), 'yyyy-MM-dd HH:mm:ss'), LastSeen=format_datetime(max(timestamp), 'yyyy-MM-dd HH:mm:ss')"
            },
            "authentication": {
              "type": "ManagedServiceIdentity",
              "audience": "https://api.applicationinsights.io"
            }
          },
          "runAfter": {}
        },
        "Post_Exception_to_Slack": {
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
                    "text": "@{if(equals(triggerBody()?['data']?['essentials']?['monitorCondition'], 'Resolved'), concat('✅ Resolved – ', triggerBody()?['data']?['essentials']?['alertRule']), concat('🚨 Exception – ', triggerBody()?['data']?['essentials']?['alertRule']))}",
                    "emoji": true
                  }
                },
                {
                  "type": "section",
                  "fields": [
                    {
                      "type": "mrkdwn",
                      "text": "@{concat('*Environment*\n`', toUpper(split(triggerBody()?['data']?['essentials']?['alertRule'], '-')[1]), '`')}"
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
                      "text": "@{concat('*Exception Type*\n`', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[1], 'N/A'), '` ×', string(coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[0], 0)))}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "@{concat('*Affected URL*\n`', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[3], 'N/A'), '`')}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "@{concat('*Cloud Role*\n`', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[5], 'N/A'), '`')}"
                    },
                    {
                      "type": "mrkdwn",
                      "text": "@{concat('*Time Range*\n', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[6], 'N/A'), ' → ', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[7], 'N/A'))}"
                    }
                  ]
                },
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "@{concat('*Message*\n> ', coalesce(body('Query_App_Insights')?['tables']?[0]?['rows']?[0]?[2], 'N/A'))}"
                  }
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
            "Query_App_Insights": ["Succeeded", "Failed", "Skipped", "TimedOut"]
          }
        }
      },
      "else": {
        "actions": {
          "Post_Infrastructure_to_Slack": {
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
                      "text": "@{if(equals(triggerBody()?['data']?['essentials']?['monitorCondition'], 'Resolved'), concat('✅ Resolved – ', triggerBody()?['data']?['essentials']?['alertRule']), concat('⚠️ Alert – ', triggerBody()?['data']?['essentials']?['alertRule']))}",
                      "emoji": true
                    }
                  },
                  {
                    "type": "section",
                    "fields": [
                      {
                        "type": "mrkdwn",
                        "text": "@{concat('*Resource*\n`', coalesce(triggerBody()?['data']?['essentials']?['configurationItems']?[0], 'N/A'), '`')}"
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
                    "type": "section",
                    "text": {
                      "type": "mrkdwn",
                      "text": "@{concat('*Description*\n> ', coalesce(triggerBody()?['data']?['essentials']?['description'], 'N/A'))}"
                    }
                  },
                  {
                    "type": "divider"
                  },
                  {
                    "type": "section",
                    "fields": [
                      {
                        "type": "mrkdwn",
                        "text": "@{concat('*Metric*\n`', coalesce(triggerBody()?['data']?['alertContext']?['condition']?['allOf']?[0]?['metricName'], 'N/A'), '`')}"
                      },
                      {
                        "type": "mrkdwn",
                        "text": "@{concat('*Current Value*\n', string(coalesce(triggerBody()?['data']?['alertContext']?['condition']?['allOf']?[0]?['metricValue'], 'N/A')), ' (', coalesce(triggerBody()?['data']?['alertContext']?['condition']?['allOf']?[0]?['operator'], ''), ' ', string(coalesce(triggerBody()?['data']?['alertContext']?['condition']?['allOf']?[0]?['threshold'], 'N/A')), ')')}"
                      },
                      {
                        "type": "mrkdwn",
                        "text": "@{concat('*Aggregation*\n', coalesce(triggerBody()?['data']?['alertContext']?['condition']?['allOf']?[0]?['timeAggregation'], 'N/A'))}"
                      }
                    ]
                  },
                  {
                    "type": "section",
                    "text": {
                      "type": "mrkdwn",
                      "text": "@{concat(':azure: <', triggerBody()?['data']?['essentials']?['portalLink'], '|View Alert>')}"
                    }
                  }
                ]
              }
            },
            "runAfter": {}
          }
        }
      },
      "runAfter": {}
    }
  BODY

  depends_on = [azurerm_logic_app_trigger_http_request.azure_monitor_alert]
}
