module "db_setup" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-dbm-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  container_command = ["/bin/sh", "-c"]

  container_args = [
    var.seed_demo_data
    ? "python manage.py migrate && python manage.py seed_demo_data --noinput"
    : "python manage.py migrate"
  ]
  docker_image = var.docker_image
  user_assigned_identity_ids = flatten([
    [module.azure_blob_storage_identity.id],
    [module.azure_queue_storage_identity.id],
    var.deploy_database_as_container ? [] : [module.db_connect_identity[0].id]
  ])
  environment_variables = merge(
    local.common_env,
    var.deploy_database_as_container ? local.container_db_env : local.azure_db_env,
    { APPLICATIONINSIGHTS_IS_ENABLED = "False" },
  )
  secret_variables = var.deploy_database_as_container ? { DATABASE_PASSWORD = resource.random_password.admin_password[0].result } : {}

  # alerts
  action_group_id            = var.action_group_id
  enable_alerting            = var.enable_alerting
  log_analytics_workspace_id = var.log_analytics_workspace_id

  depends_on = [
    module.queue_storage_role_assignment,
    module.blob_storage_role_assignment
  ]

}
