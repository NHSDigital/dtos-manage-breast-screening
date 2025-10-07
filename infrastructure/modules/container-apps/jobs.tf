locals {
  scheduled_jobs = {
    store_mesh_messages = {
      cron_expression = "*/15 * * * *"
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-mesh-data"
      }
      job_short_name     = "smm"
      job_container_args = "store_mesh_messages"
    }
    create_appointments = {
      cron_expression = local.NO_OP_DATE
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-mesh-data"
      }
      job_short_name     = "cap"
      job_container_args = "create_appointments"
    }
    send_message_batch = {
      cron_expression = local.NO_OP_DATE
      environment_variables = {
        API_OAUTH_TOKEN_URL              = var.api_oauth_token_url
        NHS_NOTIFY_API_MESSAGE_BATCH_URL = var.nhs_notify_api_message_batch_url
        RETRY_QUEUE_NAME                 = "notifications-message-batch-retries"
      }
      job_short_name     = "smb"
      job_container_args = "send_message_batch"
    }
    retry_failed_message_batch = {
      cron_expression = local.NO_OP_DATE
      environment_variables = {
        API_OAUTH_TOKEN_URL              = var.api_oauth_token_url
        NHS_NOTIFY_API_MESSAGE_BATCH_URL = var.nhs_notify_api_message_batch_url
        RETRY_QUEUE_NAME                 = "notifications-message-batch-retries"
      }
      job_short_name     = "rmb"
      job_container_args = "retry_failed_message_batch"
    }
    save_message_status = {
      cron_expression = local.NO_OP_DATE
      environment_variables = {
        STATUS_UPDATES_QUEUE_NAME = "notifications-message-status-updates"
      }
      job_short_name     = "sms"
      job_container_args = "save_message_status"
    }
    create_failures_report = {
      cron_expression = local.NO_OP_DATE
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-reports"
      }
      job_short_name     = "crf"
      job_container_args = "create_report"
    }
    create_aggregate_report = {
      cron_expression = local.NO_OP_DATE
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-reports"
      }
      job_short_name     = "cra"
      job_container_args = "create_report aggregate"
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
  secret_variables = var.deploy_database_as_container ? { DATABASE_PASSWORD = resource.random_password.admin_password[0].result } : {}
  docker_image     = var.docker_image
  user_assigned_identity_ids = flatten([
    [module.azure_blob_storage_identity.id],
    [module.azure_queue_storage_identity.id],
    var.deploy_database_as_container ? [] : [module.db_connect_identity[0].id]
  ])
  environment_variables = merge(
    local.common_env,
    var.deploy_database_as_container ? local.container_db_env : local.azure_db_env
  )
  depends_on = [
    module.queue_storage_role_assignment,
    module.blob_storage_role_assignment
  ]

}

module "scheduled_jobs" {
  source   = "../dtos-devops-templates/infrastructure/modules/container-app-job"
  for_each = local.scheduled_jobs

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

  # Ensure RBAC role assignments are created before the job definition finalizes
  depends_on = [
    module.blob_storage_role_assignment,
    module.queue_storage_role_assignment
  ]

  cron_expression = each.value.cron_expression
}
