locals {
  scheduled_jobs = {
    # Reads and acknowledges messages (DAT files) in MESH
    # Stores the files in Azure Blob Storage. Executes every 15 minutes.
    store_mesh_data = {
      cron_expression = "*/15 * * * *"
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-mesh-data"
      }
      job_short_name     = "smd"
      job_container_args = "store_mesh_data"
    }
    # Reads file data from Azure Blob Storage
    # Inserts or updates records in Postgresql. Executes every 30 minutes.
    create_appointments = {
      cron_expression = "*/30 * * * *"
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-mesh-data"
      }
      job_short_name     = "cap"
      job_container_args = "create_appointments"
    }

    # Reads appointment data from Postgresql
    # Makes a message batch request to NHS Notify. Executes daily at 1100, 1300 and 1500.
    send_message_batch = {
      cron_expression = "0 11,13,15 * * *"
      environment_variables = {
        API_MESSAGE_BATCH_URL = var.nhs_notify_api_message_batch_url
        RETRY_QUEUE_NAME      = "notifications-message-batch-retries"
      }
      job_short_name     = "smb"
      job_container_args = "send_message_batch"
    }
    # Retries messahe batches which failed to send via NHS Notify.
    # Executes every 30 minutes.
    retry_failed_message_batch = {
      cron_expression = "*/30 * * * *"
      environment_variables = {
        API_MESSAGE_BATCH_URL = var.nhs_notify_api_message_batch_url
        RETRY_QUEUE_NAME      = "notifications-message-batch-retries"
      }
      job_short_name     = "rmb"
      job_container_args = "retry_failed_message_batch"
    }
    # Fetches message statuses from Azure Storage Queue.
    # Saves statuses to the database. Executes every 30 minutes.
    save_message_status = {
      cron_expression = "*/30 * * * *"
      environment_variables = {
        API_MESSAGE_BATCH_URL     = var.nhs_notify_api_message_batch_url
        STATUS_UPDATES_QUEUE_NAME = "message-status-updates"
      }
      job_short_name     = "sms"
      job_container_args = "save_message_status"
    }
    # Creates a report of failed messages sent to NHS Notify.
    # Stores the report in Azure blob storage. Executes daily at 2330
    create_failures_report = {
      cron_expression = "30 23 * * *"
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-reports"
      }
      job_short_name     = "crf"
      job_container_args = "create_report"
    }
    # Creates an aggregate report of messages sent in the past 3 months.
    # Stores the report in Azure blob storage. Executes daily at 2345
    create_aggregate_report = {
      cron_expression = "45 23 * * *"
      environment_variables = {
        BLOB_CONTAINER_NAME = "notifications-reports"
      }
      job_short_name     = "cra"
      job_container_args = "create_report aggregate"
    }
  }
}

module "scheduled_jobs" {
  source   = "../dtos-devops-templates/infrastructure/modules/container-app-job"
  for_each = local.scheduled_jobs

  name                         = "${var.app_short_name}-${each.value.job_short_name}-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = var.app_key_vault_id

  # Run everything through /bin/sh
  container_command = ["/bin/sh", "-c"]
  container_args = [
    "python manage.py ${each.value.job_container_args}"
  ]

  docker_image               = var.docker_image
  user_assigned_identity_ids = [module.azure_blob_storage_identity.id, module.azure_queue_storage_identity.id, module.db_connect_identity.id]

  environment_variables = merge(each.value.environment_variables, {
    AZURE_CLIENT_ID = module.azure_blob_storage_identity.client_id
    DATABASE_HOST   = module.postgres.host
    DATABASE_NAME   = module.postgres.database_names[0]
    DATABASE_USER   = module.db_connect_identity.name
    DJANGO_ENV      = var.env_config
    SSL_MODE        = "require"
  })

  schedule_trigger_config {
    cron_expression          = each.value.cron_expression
    parallelism              = 1
    replica_completion_count = 1
  }
}
