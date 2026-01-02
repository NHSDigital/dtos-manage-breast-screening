locals {
  scheduled_jobs = {
    store_mesh_messages = {
      cron_expression = "0 */6 * * *"
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-mesh-data"
      }
      job_short_name     = "smm"
      job_container_args = "store_mesh_messages"
    }
    create_appointments = {
      cron_expression = "10 */6 * * *"
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-mesh-data"
      }
      job_short_name     = "cap"
      job_container_args = "create_appointments"
    }
    create_reports = {
      # cron_expression = "0 21 * * 1-5"
      cron_expression = null
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-reports"
      }
      job_short_name     = "crp"
      job_container_args = "create_reports"
    }
    smoke_test = {
      cron_expression = null
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-reports"
      }
      job_short_name     = "smk"
      job_container_args = "create_reports --smoke-test"
    }
    collect_metrics = {
      cron_expression = "*/5 * * * *"
      environment_variables = {
        ENVIRONMENT               = var.environment
      }
      job_short_name     = "clm"
      job_container_args = "collect_metrics"
    }
  }
}

module "db_setup" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-dbm-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  container_command = ["/bin/sh", "-c"]

  container_args = [
    var.seed_demo_data
    ? "python manage.py migrate && python manage.py seed_demo_data --noinput && python manage.py create_personas"
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

module "scheduled_jobs" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"
  for_each = {
    for k, v in local.scheduled_jobs : k => v
    if(var.run_notifications_smoke_test || k != "smoke_test")
  }

  name                         = "${var.app_short_name}-${each.value.job_short_name}-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = var.app_key_vault_id

  container_command = ["/bin/sh", "-c"]
  container_args = [
    "python manage.py ${each.value.job_container_args}"
  ]

  docker_image        = var.docker_image
  replica_retry_limit = 0
  user_assigned_identity_ids = flatten([
    [module.azure_blob_storage_identity.id],
    [module.azure_queue_storage_identity.id],
    var.deploy_database_as_container ? [] : [module.db_connect_identity[0].id]
  ])

  environment_variables = merge(
    local.common_env,
    {
      "STORAGE_ACCOUNT_NAME" = module.storage.storage_account_name,
      "BLOB_MI_CLIENT_ID"    = module.azure_blob_storage_identity.client_id,
      "QUEUE_MI_CLIENT_ID"   = module.azure_queue_storage_identity.client_id
    },
    each.value.environment_variables,
    var.deploy_database_as_container ? local.container_db_env : local.azure_db_env
  )
  secret_variables = merge(
    { APPLICATIONINSIGHTS_CONNECTION_STRING = var.app_insights_connection_string },
    var.deploy_database_as_container ? { DATABASE_PASSWORD = resource.random_password.admin_password[0].result } : {}
  )

  # alerts
  action_group_id            = var.action_group_id
  enable_alerting            = var.enable_alerting
  log_analytics_workspace_id = var.log_analytics_workspace_id

  # Ensure RBAC role assignments are created before the job definition finalizes
  depends_on = [
    module.blob_storage_role_assignment,
    module.queue_storage_role_assignment
  ]

  cron_expression = var.enable_notifications_jobs_schedule ? each.value.cron_expression : null
}
