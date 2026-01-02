# Metrics and logging

Some processes were setup for the `notifications` code to observe logs, events and metrics

## Application Insights

The ApplicationInsightsLogging service class sets up logs to feed into Application Insights, which can then be called like so:

```python
class CommandHandler:
    @contextmanager
    @staticmethod
    def handle(command_name):
        try:
            yield
            ApplicationInsightsLogging().custom_event_info(
                event_name=f"{command_name}Completed",
                message=f"{command_name} completed successfully",
            )
        except Exception as e:
            ApplicationInsightsLogging().exception(f"{command_name}Error: {e}")
            raise CommandError(e)
```

The Application Insights resource is setup in by the `app_insights_audit` module in terraform:

```terraform
module "app_insights_audit" {
  source = "../dtos-devops-templates/infrastructure/modules/app-insights"

  name                = module.shared_config.names.app-insights
  location            = var.region
  resource_group_name = azurerm_resource_group.main.name
  appinsights_type    = "web"

  log_analytics_workspace_id = module.log_analytics_workspace_audit.id

  # alerts
  action_group_id     = var.action_group_id
  enable_alerting     = var.enable_alerting
}
```

## Metrics

This PR introduced a Metrics service class and command to collect information about queue sizes
<https://github.com/NHSDigital/dtos-manage-breast-screening/pull/617>

The metrics would feed through to the Application Insights resource and could be viewed in the Portal.
