resource "azurerm_monitor_scheduled_query_rules_alert_v2" "failure_event" {
  count = var.enable_alerting ? 1 : 0

  auto_mitigation_enabled          = false
  description                      = "An alert triggered by a custom event batch_marked_as_failed logged in code"
  enabled                          = var.enable_alerting
  evaluation_frequency             = "PT5M"
  location                         = var.region
  name                             = "${var.app_short_name}-batch-failed-alert"
  resource_group_name              = azurerm_resource_group.main.name
  scopes                           = [var.app_insights_id]
  severity                         = 2
  skip_query_validation            = false
  target_resource_types            = ["microsoft.insights/components"]
  window_duration                  = "PT5M"
  workspace_alerts_storage_enabled = false

  action {
    action_groups = [var.action_group_id]
  }

  criteria {
    operator                = "GreaterThan"
    query                   = <<-QUERY
      customEvents
        | where name == "batch_marked_as_failed"
        | project timestamp, name
        | project-rename TimeGenerated=timestamp
      QUERY
    threshold               = 0
    time_aggregation_method = "Count"

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }
}

# IMPORTANT:
# Enable metrics store with all dimensions: https://docs.azure.cn/en-us/azure-monitor/app/metrics-overview?tabs=standard#custom-metrics-dimensions-and-preaggregation
# currently this feature is in preview.
resource "azurerm_monitor_scheduled_query_rules_alert_v2" "queue_length_high" {
  for_each = var.enable_alerting ? toset([
    "notifications-message-status-updates",
    "notifications-message-batch-retries"
  ]) : []

  name                = "${var.app_short_name}-${each.key}-${var.environment}-queue-length-high-alert"
  location            = var.region
  resource_group_name = azurerm_resource_group.main.name

  auto_mitigation_enabled = true
  description             = "Alert when queue length exceeds ${var.queue_length_alert_threshold}"
  display_name            = "${var.app_short_name} Notifications Queue Length High Alert"
  enabled                 = true
  severity                = 2
  evaluation_frequency    = "PT10M"
  window_duration         = "PT10M"
  scopes                  = [var.app_insights_id]

  criteria {
    query = <<-KQL
      customMetrics
      | where name == "queue_size_${each.key}"
      | extend environment = tostring(customDimensions.environment)
      | where environment == "${var.environment}"
      | extend value = toreal(value)
      | summarize avg_value = avg(value) by bin(timestamp, 5m)
      | where avg_value > ${var.queue_length_alert_threshold}
    KQL

    metric_measure_column   = "avg_value"
    time_aggregation_method = "Average"
    operator  = "GreaterThan"
    threshold = 0

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    action_groups = [var.action_group_id]
  }

  tags = {
    environment = var.environment
  }
}
