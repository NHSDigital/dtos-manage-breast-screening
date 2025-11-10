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
      | where name == "${each.key}"
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
