workspace {

  model {
    user = person "Staff User" {
      description "A user of the system"
    }

    cis2 = softwareSystem "CIS2" {
      description "Central authentication system used to authenticate users"
      tags external
    }

    mesh = softwareSystem "NBSS MESH mailbox" {
      description "Events from NBSS in each breast screening office"
      tags external
    }

    notify = softwareSystem "NHS Notify" {
      description "Send invitations via NHS app, SMS, post"
      tags external
    }

    azure_arc = softwareSystem "Azure ARC" "Manages external VMs at scale" {
      tags azure
    }
    azure_relay = softwareSystem "Azure relay" "Securely exposes services" {
      tags azure
    }
    azure = group "Azure" {
      breastScreeningSystem = softwareSystem "Breast Screening System" {
        webApplication = container "Manage Breast Screening" "Allows users to manage breast screening appointments and records" {
          technology "Container app Web"
        }
        azurePostgres = container "Database" "Stores screening data" {
          technology "Managed Azure postgres"
          tags database azure
        }

        jobs = container "Functions" "Process events asynchronously" {
          technology "Event driven container app jobs"
          save_message_status = component "Save message status" {
              technology "Event driven container app job"
              tags job
          }
          send_message_batch = component "Send message batch / Retry failed message batch" "2 separate jobs" {
              technology "Event driven container app job"
              tags job
          }
          create_appointments = component "Create appointments" {
              technology "Event driven container app job"
              tags job
          }
          store_mesh_messages = component "Store Mesh messages" {
              technology "Event driven container app job"
              tags job
          }
          create_report = component "Create report" {
              technology "Event driven container app job"
              tags job
          }

          mesh_blob_container = component "MESH data" {
              technology "Azure storage blob container"
              tags azure
          }
          reports_blob_container = component "Reports" {
              technology "Azure storage blob container"
              tags azure
          }
          queue = component "Message status queue" {
              technology "Azure storage queue"
              tags azure
          }
          retry_queue = component "Retry queue" {
              technology "Azure storage queue"
              tags azure
          }
        }

        webApplication -> azurePostgres "Reads from and writes to"
      }
    }

    hospital_network = group "Hospital network" {
      hospital_screening = softwareSystem "Hospital Screening system" "Deployed in each hospital or trust" {

        gw = container "Screening gateway" "VM with outbound connection to web application" {
          tags "Gateway"

          vm = component "Virtual machine" "Managed by hospital"
          arc_agent = component "Azure ARC agent" "Outbound connection to receive deployment instructions"
          gw_app = component "Gateway application" "Connects to both the API in Azure and devices in the hospital network"

          vm -> arc_agent "Runs"
          arc_agent -> gw_app "Deploys"
        }
        modality = container "Modality" {
          tags external
        }
        pacs = container "PACS" {
          tags external
        }
        erp = container "ERP/Hospital referrals" {
          tags external
        }
        labs = container "Labs" {
          tags external
        }

        gw -> modality "Imaging orders and notifications"
        gw -> pacs "Images & metadata"
        gw -> erp "Family history referrals, imaging reports"
        gw -> labs "Pathology orders and results"
      }
    }

    arc_agent -> azure_arc "Receives instructions from"
    gw_app -> azure_relay "Creates bidirectional connection to API"
    webApplication -> azure_relay "Creates bidirectional connection to gateway"
    hospital_screening -> webApplication  "Uses outbound connection to communicate back and forth with"

    user -> cis2 "Authenticates via"
    cis2 -> webApplication "Provides authentication token to"

    save_message_status -> queue "Gets updates to save"
    store_mesh_messages -> mesh "Fetches appointments from" {
      tags store_mesh
    }
    send_message_batch -> notify "Sends message requests"
    send_message_batch -> retry_queue "Sends failed batches" {
      tags send_retry
    }
    create_appointments -> mesh_blob_container "Gets MESH messages"
    store_mesh_messages -> mesh_blob_container "Stores MESH messages"
    create_report -> reports_blob_container "Stores message status reports"
    notify -> webApplication "Sends status updates to"
    webApplication -> queue "Save message status"

    # Commented to avoid cluttering - Grouped with send_message_batch
    # retry_failed_message_batch -> retry_queue "Gets failed batches"
    # retry_failed_message_batch -> notify "Retry messages"

    # Commented to avoid cluttering - DB connection in view title
    # store_mesh_messages -> azurePostgres "Store messages to"
    # save_message_status -> azurePostgres "Save message status"
    # send_message_batch -> azurePostgres "Gets appointments from"
    # create_appointments -> azurePostgres "Converts to appointments and clinic"
    # create_report -> azurePostgres "Gets message statuses from"

    # Commented to avoid cluttering
    # jobs -> azurePostgres "Store data"
  }

  views {

    systemContext breastScreeningSystem {
      include * user
      exclude azure_relay
      autolayout lr
    }

    container breastScreeningSystem {
      include "element.parent==breastScreeningSystem" mesh notify cis2 azure_relay
      exclude "webApplication->jobs"
      autolayout tb
    }

    container hospital_screening {
      include *
      autolayout tb
    }

    component jobs {
      title "Functions [Connections to database are omitted]"
      include *
      autolayout tb
    }

    component gw {
      include *
      autolayout bt 150
    }

    styles {
      element external {
        background #AAAAAA
      }
      element database {
        shape Cylinder
      }
      element "Gateway" {
        shape Ellipse
      }
      element job {
        background green
        colour white
      }
      element azure {
        background blue
        colour white
      }
      relationship store_mesh {
        position 60
      }
      relationship send_retry {
        position 20
      }
    }

    theme default
  }
}
