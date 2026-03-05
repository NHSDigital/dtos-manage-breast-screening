workspace {

  model {
    user = person "Staff User" {
      description "A user of the system"
    }

    cis2 = softwareSystem "CIS2" {
      description "Central authentication system used to authenticate users"
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
  }

  views {

    systemContext breastScreeningSystem {
      include * user
      exclude azure_relay
      autolayout lr 350 150
    }

    container breastScreeningSystem {
      include "element.parent==breastScreeningSystem" cis2 azure_relay
      autolayout tb
    }

    container hospital_screening {
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
    }

    theme default
  }
}
