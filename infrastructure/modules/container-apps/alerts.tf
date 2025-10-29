resource "azurerm_monitor_scheduled_query_rules_alert_v2" "failure_event" {
  count = var.enable_alerting ? 1 : 0

  auto_mitigation_enabled           = false
  description                       = "An alert triggered by a custom event batch_marked_as_failed logged in code"
  enabled                           = var.enable_alerting
  evaluation_frequency              = "PT5M"
  location                          = var.region
  name                              = "${var.app_short_name}-batch-failed-alert"
  resource_group_name               = azurerm_resource_group.main.name
  scopes                            = [var.app_insights_id]
  severity                          = 2
  skip_query_validation             = false
  target_resource_types             = ["microsoft.insights/components"]
  window_duration                   = "PT5M"
  workspace_alerts_storage_enabled  = false

  action {
    action_groups     = [var.action_group_id]
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
