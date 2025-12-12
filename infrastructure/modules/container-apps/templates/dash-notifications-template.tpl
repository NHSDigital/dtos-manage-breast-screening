{
  "lenses": {
    "0": {
      "order": 0,
      "parts": {
        "0": {
          "position": {
            "x": 0,
            "y": 0,
            "colSpan": 3,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "content": "",
                "title": "General performance",
                "subtitle": "",
                "markdownSource": 1,
                "markdownUri": ""
              }
            }
          }
        },
        "1": {
          "position": {
            "x": 4,
            "y": 1,
            "colSpan": 4,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "ResourceId",
                "value": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs"
              },
              {
                "name": "ComponentId",
                "value": {
                  "SubscriptionId": "${sub_id}",
                  "ResourceGroup": "rg-manbrs-${environment}-uks",
                  "Name": "appi-${environment}-uks-manbrs",
                  "LinkedApplicationType": 0,
                  "ResourceId": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs",
                  "ResourceType": "microsoft.insights/components",
                  "IsAzureFirst": false
                }
              },
              {
                "name": "TargetBlade",
                "value": "Failures"
              },
              {
                "name": "DataModel",
                "value": {
                  "version": "1.0.0",
                  "experience": 3,
                  "clientTypeMode": "Server",
                  "timeContext": {
                    "durationMs": 86400000,
                    "createdTime": "2025-10-17T14:38:39.283Z",
                    "isInitialTime": false,
                    "grain": 1,
                    "useDashboardTimeRange": false
                  },
                  "prefix": "let OperationIdsWithExceptionType = (excType: string) { exceptions | where timestamp > ago(1d) \n    | where tobool(iff(excType == \"null\", isempty(type), type == excType)) \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedReqResponseCode = (respCode: string) { requests | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct id };\nlet OperationIdsWithFailedDependencyType = (depType: string) { dependencies | where timestamp > ago(1d)\n    | where iff(depType == \"null\", isempty(type), type == depType) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedDepResponseCode = (respCode: string) { dependencies | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithExceptionBrowser = (browser: string) { exceptions | where timestamp > ago(1d)\n    | where tobool(iff(browser == \"null\", isempty(client_Browser), client_Browser == browser)) \n    | distinct operation_ParentId };",
                  "grain": "5m",
                  "selectedOperation": null,
                  "selectedOperationName": null,
                  "filters": []
                },
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "1.0"
              }
            ],
            "type": "Extension/AppInsightsExtension/PartType/FailuresCuratedPinnedChartPart",
            "asset": {
              "idInputName": "ResourceId",
              "type": "ApplicationInsights"
            },
            "partHeader": {
              "title": "Total Exceptions",
              "subtitle": ""
            }
          }
        },
        "2": {
          "position": {
            "x": 8,
            "y": 1,
            "colSpan": 4,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "ResourceId",
                "value": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs"
              },
              {
                "name": "ComponentId",
                "value": {
                  "SubscriptionId": "${sub_id}",
                  "ResourceGroup": "rg-manbrs-${environment}-uks",
                  "Name": "appi-${environment}-uks-manbrs",
                  "LinkedApplicationType": 0,
                  "ResourceId": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs",
                  "ResourceType": "microsoft.insights/components",
                  "IsAzureFirst": false
                }
              },
              {
                "name": "TargetBlade",
                "value": "Performance"
              },
              {
                "name": "DataModel",
                "value": {
                  "version": "1.0.0",
                  "experience": 1,
                  "clientTypeMode": "Server",
                  "timeContext": {
                    "durationMs": 2592000000
                  },
                  "prefix": "let OperationIdsWithExceptionType = (excType: string) { exceptions | where timestamp > ago(30d) \n    | where tobool(iff(excType == \"null\", isempty(type), type == excType)) \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedReqResponseCode = (respCode: string) { requests | where timestamp > ago(30d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct id };\nlet OperationIdsWithFailedDependencyType = (depType: string) { dependencies | where timestamp > ago(30d)\n    | where iff(depType == \"null\", isempty(type), type == depType) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedDepResponseCode = (respCode: string) { dependencies | where timestamp > ago(30d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithExceptionBrowser = (browser: string) { exceptions | where timestamp > ago(30d)\n    | where tobool(iff(browser == \"null\", isempty(client_Browser), client_Browser == browser)) \n    | distinct operation_ParentId };",
                  "percentile": 1,
                  "grain": "1d",
                  "selectedOperation": null,
                  "selectedOperationName": null,
                  "filters": [
                    {
                      "kql": "iif( itemType == \"request\", (column_ifexists(\"operation_Name\", \"\") contains \"POST\"), (itemType == \"request\" and column_ifexists(\"id\", operation_ParentId) in ((requests | where timestamp > datetime(\"2025-10-12T15:13:32.269Z\") and timestamp < datetime(\"2025-11-11T15:13:32.269Z\")| where operation_Name contains \"POST\" | distinct id | limit 1000000))) \nor (itemType != \"request\" and operation_ParentId in ((requests | where timestamp > datetime(\"2025-10-12T15:13:32.269Z\") and timestamp < datetime(\"2025-11-11T15:13:32.269Z\")| where operation_Name contains \"POST\" | distinct id | limit 1000000))))",
                      "table": "requests",
                      "name": "operation_Name",
                      "operator": "contains",
                      "values": [
                        "POST"
                      ],
                      "builtIn": false,
                      "canEdit": true,
                      "timeContext": {
                        "durationMs": 2592000000
                      }
                    },
                    {
                      "kql": "iif( itemType == \"request\", (column_ifexists(\"resultCode\", \"\") == \"200\"), (itemType == \"request\" and column_ifexists(\"id\", operation_ParentId) in ((requests | where timestamp > datetime(\"2025-10-12T15:13:32.269Z\") and timestamp < datetime(\"2025-11-11T15:13:32.269Z\")| where resultCode == \"200\" | distinct id | limit 1000000))) \nor (itemType != \"request\" and operation_ParentId in ((requests | where timestamp > datetime(\"2025-10-12T15:13:32.269Z\") and timestamp < datetime(\"2025-11-11T15:13:32.269Z\")| where resultCode == \"200\" | distinct id | limit 1000000))))",
                      "table": "requests",
                      "name": "resultCode",
                      "operator": "==",
                      "values": [
                        "200"
                      ],
                      "builtIn": false,
                      "canEdit": true,
                      "timeContext": {
                        "durationMs": 2592000000
                      }
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "1.0"
              }
            ],
            "type": "Extension/AppInsightsExtension/PartType/PerformanceCuratedPinnedChartPart",
            "asset": {
              "idInputName": "ResourceId",
              "type": "ApplicationInsights"
            }
          }
        },
        "3": {
          "position": {
            "x": 12,
            "y": 1,
            "colSpan": 4,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "sharedTimeRange",
                "isOptional": true
              },
              {
                "name": "options",
                "value": {
                  "chart": {
                    "metrics": [
                      {
                        "resourceMetadata": {
                          "id": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-container-app-uks/providers/Microsoft.DBforPostgreSQL/flexibleServers/postgres-manbrs-${environment}-uks"
                        },
                        "name": "cpu_percent",
                        "aggregationType": 4,
                        "namespace": "microsoft.dbforpostgresql/flexibleservers",
                        "metricVisualization": {
                          "displayName": "CPU percent"
                        }
                      }
                    ],
                    "title": "Avg CPU percent for postgres-manbrs-${environment}-uks",
                    "titleKind": 1,
                    "visualization": {
                      "chartType": 2,
                      "legendVisualization": {
                        "isVisible": true,
                        "position": 2,
                        "hideHoverCard": false,
                        "hideLabelNames": true
                      },
                      "axisVisualization": {
                        "x": {
                          "isVisible": true,
                          "axisType": 2
                        },
                        "y": {
                          "isVisible": true,
                          "axisType": 1
                        }
                      }
                    },
                    "timespan": {
                      "relative": {
                        "duration": 86400000
                      },
                      "showUTCTime": false,
                      "grain": 1
                    }
                  }
                },
                "isOptional": true
              }
            ],
            "type": "Extension/HubsExtension/PartType/MonitorChartPart",
            "settings": {
              "content": {
                "options": {
                  "chart": {
                    "metrics": [
                      {
                        "resourceMetadata": {
                          "id": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-container-app-uks/providers/Microsoft.DBforPostgreSQL/flexibleServers/postgres-manbrs-${environment}-uks"
                        },
                        "name": "cpu_percent",
                        "aggregationType": 4,
                        "namespace": "microsoft.dbforpostgresql/flexibleservers",
                        "metricVisualization": {
                          "displayName": "CPU percent"
                        }
                      }
                    ],
                    "title": "Avg CPU percent for postgres-manbrs-${environment}-uks",
                    "titleKind": 1,
                    "visualization": {
                      "chartType": 2,
                      "legendVisualization": {
                        "isVisible": true,
                        "position": 2,
                        "hideHoverCard": false,
                        "hideLabelNames": true
                      },
                      "axisVisualization": {
                        "x": {
                          "isVisible": true,
                          "axisType": 2
                        },
                        "y": {
                          "isVisible": true,
                          "axisType": 1
                        }
                      },
                      "disablePinning": true
                    }
                  }
                }
              }
            },
            "filters": {
              "MsPortalFx_TimeRange": {
                "model": {
                  "format": "local",
                  "granularity": "auto",
                  "relative": "1440m"
                }
              }
            }
          }
        },
        "4": {
          "position": {
            "x": 0,
            "y": 3,
            "colSpan": 3,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "content": "",
                "title": "StoreMeshMessages",
                "subtitle": "",
                "markdownSource": 1,
                "markdownUri": ""
              }
            }
          }
        },
        "5": {
          "position": {
            "x": 3,
            "y": 3,
            "colSpan": 2,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/microsoft.insights/components/appi-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "11dabd0c-0a26-47e0-9a4f-caef62119694",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "customEvents\n| where name has \"CreateReportsCompleted\"\n| summarize count()\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "appi-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "Query": "customEvents\n| where name has \"StoreMeshMessagesCompleted\"\n| summarize count()\n\n",
                "PartTitle": "Jobs completed (smm)"
              }
            },
            "partHeader": {
              "title": "Jobs completed (smm)",
              "subtitle": ""
            }
          }
        },
        "6": {
          "position": {
            "x": 6,
            "y": 3,
            "colSpan": 3,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "content": "",
                "title": "RetryFailedMessageBatches",
                "subtitle": "",
                "markdownSource": 1,
                "markdownUri": ""
              }
            },
            "partHeader": {
              "title": "CreateAppointments"
            }
          }
        },
        "7": {
          "position": {
            "x": 9,
            "y": 3,
            "colSpan": 2,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/microsoft.insights/components/appi-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "11dabd0c-0a26-47e0-9a4f-caef62119694",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "customEvents\n| where name has \"CreateReportsCompleted\"\n| summarize count()\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "appi-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "Query": "customEvents\n| where name has \"CreateAppointmentsCompleted\"\n| summarize count()\n\n",
                "PartTitle": "Jobs completed (cap)"
              }
            },
            "partHeader": {
              "title": "Jobs completed (cap)",
              "subtitle": ""
            }
          }
        },
        "8": {
          "position": {
            "x": 0,
            "y": 4,
            "colSpan": 3,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "content": "https://portal.azure.com#@50f6071f-bbfe-401a-8803-673748e629e2/blade/Microsoft_OperationsManagementSuite_Workspace/Logs.ReactView/resourceId/%2Fsubscriptions%2F${sub_id}%2Fresourcegroups%2Frg-manbrs-${environment}-uks%2Fproviders%2Fmicrosoft.operationalinsights%2Fworkspaces%2Flaw-${environment}-uks-manbrs/source/LogsBlade.AnalyticsShareLinkToQuery/q/H4sIAAAAAAAAA0WNOw7CMAyG957CW5dyCJShS8XEHpn2Fw3CcWQbdeHwREKI%252FXskrcGlws6tJa2uTyx695yW4U3HDgOlHzKbvtqFBdnJgy38KLHTKFxv5icXGbvUTB9Yg65FMKNrHNimf%252BUbmKhvsn8Ax4DDvH8AAAA%253D/timespan/P1D/limit/1000",
                "title": "Container logs (smm)",
                "subtitle": "",
                "markdownSource": 1,
                "markdownUri": ""
              }
            }
          }
        },
        "9": {
          "position": {
            "x": 6,
            "y": 4,
            "colSpan": 3,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "content": "https://portal.azure.com#@50f6071f-bbfe-401a-8803-673748e629e2/blade/Microsoft_OperationsManagementSuite_Workspace/Logs.ReactView/resourceId/%2Fsubscriptions%2F${sub_id}%2Fresourcegroups%2Frg-manbrs-${environment}-uks%2Fproviders%2Fmicrosoft.operationalinsights%2Fworkspaces%2Flaw-${environment}-uks-manbrs/source/LogsBlade.AnalyticsShareLinkToQuery/q/H4sIAAAAAAAAA0WNOw7CMAyGd07hrUs5BMrQpWJij0z51QaR2LKNuvTwREKI%252FXskacGlwS6qSZrLC7OsntN8OmjfYKD0QyaTt165Ijt5sIXvJTYaKre7%252BXlhHbqkJk8sQbdSMaFrHHiM%252F8o3MFLfZP8A5AIGwn8AAAA%253D/timespan/P1D/limit/1000",
                "title": "Container logs (cap)",
                "subtitle": "",
                "markdownSource": 1,
                "markdownUri": ""
              }
            }
          }
        },
        "10": {
          "position": {
            "x": 0,
            "y": 5,
            "colSpan": 2,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.OperationalInsights/workspaces/law-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "13b7cc3c-0f61-4ade-a127-775146122831",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P3D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-smm'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has \"stored in blob storage\"\n| summarize count()\n\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "law-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {},
            "partHeader": {
              "title": "Msgs saved to blob",
              "subtitle": ""
            }
          }
        },
        "11": {
          "position": {
            "x": 6,
            "y": 5,
            "colSpan": 2,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.OperationalInsights/workspaces/law-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "1357b321-a63d-40ae-9686-e52bb59a71fb",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-cap'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has \"Processing blob\"\n| summarize count()\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "law-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {},
            "partHeader": {
              "title": "Blobs processed",
              "subtitle": ""
            }
          }
        },
        "12": {
          "position": {
            "x": 8,
            "y": 5,
            "colSpan": 3,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.OperationalInsights/workspaces/law-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "1114036f-75a5-43a0-b215-a66e68358bfc",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-cap'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has_all(\"created\",\"Appointment\")\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "law-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "Query": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-cap'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has_all(\"created\",\"Appointment\")\n| summarize count() by bin(TimeGenerated, 1day)\n\n"
              }
            },
            "partHeader": {
              "title": "Appt. created",
              "subtitle": ""
            }
          }
        },
        "13": {
          "position": {
            "x": 11,
            "y": 5,
            "colSpan": 3,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.OperationalInsights/workspaces/law-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "093720e4-d6fb-4391-8110-0a38251053b7",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-cap'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has_all(\"cancelled\",\"Appointment\")\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "law-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "Query": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-cap'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has_all(\"cancelled\",\"Appointment\")\n| summarize count() by bin(TimeGenerated, 1day)\n\n"
              }
            },
            "partHeader": {
              "title": "Appt. cancelled",
              "subtitle": ""
            }
          }
        },
        "14": {
          "position": {
            "x": 14,
            "y": 5,
            "colSpan": 4,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.OperationalInsights/workspaces/law-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "151602f6-15c2-46c4-a131-3dd898866ab6",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-cap'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has_all(\"marked completed\",\"Appointment\")\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "law-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "GridColumnsWidth": {
                  "TimeGenerated": "252px"
                },
                "Query": "ContainerAppConsoleLogs_CL\n| where ContainerGroupName_s startswith 'manbrs-cap'\n| project TimeGenerated, ContainerName_s, Log_s\n| where Log_s has_all(\"marked completed\",\"Appointment\")\n| summarize count() by bin(TimeGenerated, 1day)\n\n"
              }
            },
            "partHeader": {
              "title": "Appt. completed",
              "subtitle": ""
            }
          }
        },
        "15": {
          "position": {
            "x": 0,
            "y": 7,
            "colSpan": 4,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "ResourceId",
                "value": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs"
              },
              {
                "name": "ComponentId",
                "value": {
                  "SubscriptionId": "${sub_id}",
                  "ResourceGroup": "rg-manbrs-${environment}-uks",
                  "Name": "appi-${environment}-uks-manbrs",
                  "LinkedApplicationType": 0,
                  "ResourceId": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs",
                  "ResourceType": "microsoft.insights/components",
                  "IsAzureFirst": false
                }
              },
              {
                "name": "TargetBlade",
                "value": "Failures"
              },
              {
                "name": "DataModel",
                "value": {
                  "version": "1.0.0",
                  "experience": 3,
                  "clientTypeMode": "Server",
                  "timeContext": {
                    "durationMs": 86400000,
                    "createdTime": "2025-10-24T14:15:20.797Z",
                    "isInitialTime": false,
                    "grain": 1,
                    "useDashboardTimeRange": false
                  },
                  "prefix": "let OperationIdsWithExceptionType = (excType: string) { exceptions | where timestamp > ago(1d) \n    | where tobool(iff(excType == \"null\", isempty(type), type == excType)) \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedReqResponseCode = (respCode: string) { requests | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct id };\nlet OperationIdsWithFailedDependencyType = (depType: string) { dependencies | where timestamp > ago(1d)\n    | where iff(depType == \"null\", isempty(type), type == depType) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedDepResponseCode = (respCode: string) { dependencies | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithExceptionBrowser = (browser: string) { exceptions | where timestamp > ago(1d)\n    | where tobool(iff(browser == \"null\", isempty(client_Browser), client_Browser == browser)) \n    | distinct operation_ParentId };",
                  "grain": "5m",
                  "selectedOperation": null,
                  "selectedOperationName": null,
                  "filters": [
                    {
                      "kql": "iif( itemType == \"exception\", (column_ifexists(\"outerMessage\", \"\") contains \"StoreMeshMessagesError\"), (itemType == \"request\" and column_ifexists(\"id\", operation_ParentId) in ((exceptions | where timestamp > datetime(\"2025-10-23T14:16:56.849Z\") and timestamp < datetime(\"2025-10-24T14:16:56.849Z\")| where outerMessage contains \"StoreMeshMessagesError\" | distinct operation_ParentId | limit 1000000))) \nor (itemType != \"request\" and operation_ParentId in ((exceptions | where timestamp > datetime(\"2025-10-23T14:16:56.849Z\") and timestamp < datetime(\"2025-10-24T14:16:56.849Z\")| where outerMessage contains \"StoreMeshMessagesError\" | distinct operation_ParentId | limit 1000000))))",
                      "table": "exceptions",
                      "name": "outerMessage",
                      "operator": "contains",
                      "values": [
                        "StoreMeshMessagesError"
                      ],
                      "builtIn": false,
                      "canEdit": true,
                      "timeContext": {
                        "durationMs": 86400000,
                        "createdTime": "2025-10-24T14:15:20.797Z",
                        "isInitialTime": false,
                        "grain": 1,
                        "useDashboardTimeRange": false
                      }
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "1.0"
              }
            ],
            "type": "Extension/AppInsightsExtension/PartType/FailuresCuratedPinnedChartPart",
            "asset": {
              "idInputName": "ResourceId",
              "type": "ApplicationInsights"
            }
          }
        },
        "16": {
          "position": {
            "x": 6,
            "y": 7,
            "colSpan": 4,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "ResourceId",
                "value": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs"
              },
              {
                "name": "ComponentId",
                "value": {
                  "SubscriptionId": "${sub_id}",
                  "ResourceGroup": "rg-manbrs-${environment}-uks",
                  "Name": "appi-${environment}-uks-manbrs",
                  "LinkedApplicationType": 0,
                  "ResourceId": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs",
                  "ResourceType": "microsoft.insights/components",
                  "IsAzureFirst": false
                }
              },
              {
                "name": "TargetBlade",
                "value": "Failures"
              },
              {
                "name": "DataModel",
                "value": {
                  "version": "1.0.0",
                  "experience": 3,
                  "clientTypeMode": "Server",
                  "timeContext": {
                    "durationMs": 86400000,
                    "createdTime": "2025-10-17T14:38:39.283Z",
                    "isInitialTime": false,
                    "grain": 1,
                    "useDashboardTimeRange": false
                  },
                  "prefix": "let OperationIdsWithExceptionType = (excType: string) { exceptions | where timestamp > ago(1d) \n    | where tobool(iff(excType == \"null\", isempty(type), type == excType)) \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedReqResponseCode = (respCode: string) { requests | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct id };\nlet OperationIdsWithFailedDependencyType = (depType: string) { dependencies | where timestamp > ago(1d)\n    | where iff(depType == \"null\", isempty(type), type == depType) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedDepResponseCode = (respCode: string) { dependencies | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithExceptionBrowser = (browser: string) { exceptions | where timestamp > ago(1d)\n    | where tobool(iff(browser == \"null\", isempty(client_Browser), client_Browser == browser)) \n    | distinct operation_ParentId };",
                  "grain": "5m",
                  "selectedOperation": null,
                  "selectedOperationName": null,
                  "filters": [
                    {
                      "kql": "iif( itemType == \"exception\", (column_ifexists(\"outerMessage\", \"\") contains \"CreateAppointmentsError\"), (itemType == \"request\" and column_ifexists(\"id\", operation_ParentId) in ((exceptions | where timestamp > datetime(\"2025-10-16T14:39:48.835Z\") and timestamp < datetime(\"2025-10-17T14:39:48.835Z\")| where outerMessage contains \"CreateAppointmentsError\" | distinct operation_ParentId | limit 1000000))) \nor (itemType != \"request\" and operation_ParentId in ((exceptions | where timestamp > datetime(\"2025-10-16T14:39:48.835Z\") and timestamp < datetime(\"2025-10-17T14:39:48.835Z\")| where outerMessage contains \"CreateAppointmentsError\" | distinct operation_ParentId | limit 1000000))))",
                      "table": "exceptions",
                      "name": "outerMessage",
                      "operator": "contains",
                      "values": [
                        "CreateAppointmentsError"
                      ],
                      "builtIn": false,
                      "canEdit": true,
                      "timeContext": {
                        "durationMs": 86400000,
                        "createdTime": "2025-10-17T14:38:39.283Z",
                        "isInitialTime": false,
                        "grain": 1,
                        "useDashboardTimeRange": false
                      }
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "1.0"
              }
            ],
            "type": "Extension/AppInsightsExtension/PartType/FailuresCuratedPinnedChartPart",
            "asset": {
              "idInputName": "ResourceId",
              "type": "ApplicationInsights"
            },
            "partHeader": {
              "title": "Create Appointments Exceptions",
              "subtitle": ""
            }
          }
        },
        "17": {
          "position": {
            "x": 0,
            "y": 9,
            "colSpan": 3,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "content": "",
                "title": "CreateReports",
                "subtitle": "",
                "markdownSource": 1,
                "markdownUri": ""
              }
            },
            "partHeader": {
              "title": "CreateReports"
            }
          }
        },
        "18": {
          "position": {
            "x": 3,
            "y": 9,
            "colSpan": 2,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "resourceTypeMode",
                "isOptional": true
              },
              {
                "name": "ComponentId",
                "isOptional": true
              },
              {
                "name": "Scope",
                "value": {
                  "resourceIds": [
                    "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/microsoft.insights/components/appi-${environment}-uks-manbrs"
                  ]
                },
                "isOptional": true
              },
              {
                "name": "PartId",
                "value": "11dabd0c-0a26-47e0-9a4f-caef62119694",
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "2.0",
                "isOptional": true
              },
              {
                "name": "TimeRange",
                "value": "P1D",
                "isOptional": true
              },
              {
                "name": "DashboardId",
                "isOptional": true
              },
              {
                "name": "DraftRequestParameters",
                "isOptional": true
              },
              {
                "name": "Query",
                "value": "customEvents\n| where name has \"CreateReportsCompleted\"\n| summarize count()\n",
                "isOptional": true
              },
              {
                "name": "ControlType",
                "value": "AnalyticsGrid",
                "isOptional": true
              },
              {
                "name": "SpecificChart",
                "isOptional": true
              },
              {
                "name": "PartTitle",
                "value": "Analytics",
                "isOptional": true
              },
              {
                "name": "PartSubTitle",
                "value": "appi-${environment}-uks-manbrs",
                "isOptional": true
              },
              {
                "name": "Dimensions",
                "isOptional": true
              },
              {
                "name": "LegendOptions",
                "isOptional": true
              },
              {
                "name": "IsQueryContainTimeRange",
                "value": false,
                "isOptional": true
              }
            ],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "PartTitle": "Jobs completed (crp)"
              }
            },
            "partHeader": {
              "title": "Jobs completed (crp)",
              "subtitle": ""
            }
          }
        },
        "19": {
          "position": {
            "x": 0,
            "y": 10,
            "colSpan": 3,
            "rowSpan": 1
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/HubsExtension/PartType/MarkdownPart",
            "settings": {
              "content": {
                "content": "https://portal.azure.com#@50f6071f-bbfe-401a-8803-673748e629e2/blade/Microsoft_OperationsManagementSuite_Workspace/Logs.ReactView/resourceId/%2Fsubscriptions%2F${sub_id}%2FresourceGroups%2Frg-manbrs-${environment}-uks%2Fproviders%2FMicrosoft.OperationalInsights%2Fworkspaces%2Flaw-${environment}-uks-manbrs/source/LogsBlade.AnalyticsShareLinkToQuery/q/H4sIAAAAAAAAA0WNOw7CMAyGd07hrUs5BMrQpWJij0z51QaR2LKNuvTwREKI%252FXskacGlwS6qSZrLC7OsntN8OmjfYKD0QyaTt165Ijt5sIXvJTYaKre7%252BXkxHbqkJk8sQbdSMaFrHHiM%252F8o3MFLfZP8A6xHAUn8AAAA%253D/timespan/P3D/limit/500000",
                "title": "Container logs (crp)",
                "subtitle": "",
                "markdownSource": 1,
                "markdownUri": ""
              }
            }
          }
        },
        "20": {
          "position": {
            "x": 0,
            "y": 11,
            "colSpan": 4,
            "rowSpan": 2
          },
          "metadata": {
            "inputs": [
              {
                "name": "ResourceId",
                "value": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs"
              },
              {
                "name": "ComponentId",
                "value": {
                  "SubscriptionId": "${sub_id}",
                  "ResourceGroup": "rg-manbrs-${environment}-uks",
                  "Name": "appi-${environment}-uks-manbrs",
                  "LinkedApplicationType": 0,
                  "ResourceId": "/subscriptions/${sub_id}/resourceGroups/rg-manbrs-${environment}-uks/providers/Microsoft.Insights/components/appi-${environment}-uks-manbrs",
                  "ResourceType": "microsoft.insights/components",
                  "IsAzureFirst": false
                }
              },
              {
                "name": "TargetBlade",
                "value": "Failures"
              },
              {
                "name": "DataModel",
                "value": {
                  "version": "1.0.0",
                  "experience": 3,
                  "clientTypeMode": "Server",
                  "timeContext": {
                    "durationMs": 86400000,
                    "createdTime": "2025-10-29T11:09:25.937Z",
                    "isInitialTime": false,
                    "grain": 1,
                    "useDashboardTimeRange": false
                  },
                  "prefix": "let OperationIdsWithExceptionType = (excType: string) { exceptions | where timestamp > ago(1d) \n    | where tobool(iff(excType == \"null\", isempty(type), type == excType)) \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedReqResponseCode = (respCode: string) { requests | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct id };\nlet OperationIdsWithFailedDependencyType = (depType: string) { dependencies | where timestamp > ago(1d)\n    | where iff(depType == \"null\", isempty(type), type == depType) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithFailedDepResponseCode = (respCode: string) { dependencies | where timestamp > ago(1d)\n    | where iff(respCode == \"null\", isempty(resultCode), resultCode == respCode) and success == false \n    | distinct operation_ParentId };\nlet OperationIdsWithExceptionBrowser = (browser: string) { exceptions | where timestamp > ago(1d)\n    | where tobool(iff(browser == \"null\", isempty(client_Browser), client_Browser == browser)) \n    | distinct operation_ParentId };",
                  "grain": "5m",
                  "selectedOperation": null,
                  "selectedOperationName": null,
                  "filters": [
                    {
                      "kql": "iif( itemType == \"exception\", (column_ifexists(\"outerMessage\", \"\") in (\"SaveMessageStatusError: \\'Queue\\' object has no attribute \\'client\\'\",\"CreateReportsError\")), (itemType == \"request\" and column_ifexists(\"id\", operation_ParentId) in ((exceptions | where timestamp > datetime(\"2025-11-10T16:53:58.202Z\") and timestamp < datetime(\"2025-11-11T16:53:58.202Z\")| where outerMessage in (\"SaveMessageStatusError: \\'Queue\\' object has no attribute \\'client\\'\",\"CreateReportsError\") | distinct operation_ParentId | limit 1000000))) \nor (itemType != \"request\" and operation_ParentId in ((exceptions | where timestamp > datetime(\"2025-11-10T16:53:58.202Z\") and timestamp < datetime(\"2025-11-11T16:53:58.202Z\")| where outerMessage in (\"SaveMessageStatusError: \\'Queue\\' object has no attribute \\'client\\'\",\"CreateReportsError\") | distinct operation_ParentId | limit 1000000))))",
                      "table": "exceptions",
                      "name": "outerMessage",
                      "operator": "in",
                      "values": [
                        "SaveMessageStatusError: 'Queue' object has no attribute 'client'",
                        "CreateReportsError"
                      ],
                      "builtIn": false,
                      "canEdit": true,
                      "timeContext": {
                        "durationMs": 86400000,
                        "createdTime": "2025-10-29T11:09:25.937Z",
                        "isInitialTime": false,
                        "grain": 1,
                        "useDashboardTimeRange": false
                      }
                    }
                  ]
                },
                "isOptional": true
              },
              {
                "name": "Version",
                "value": "1.0"
              }
            ],
            "type": "Extension/AppInsightsExtension/PartType/FailuresCuratedPinnedChartPart",
            "asset": {
              "idInputName": "ResourceId",
              "type": "ApplicationInsights"
            }
          }
        }
      }
    }
  },
  "metadata": {
    "model": {
      "timeRange": {
        "value": {
          "relative": {
            "duration": 24,
            "timeUnit": 1
          }
        },
        "type": "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
      },
      "filterLocale": {
        "value": "en-us"
      },
      "filters": {
        "value": {
          "MsPortalFx_TimeRange": {
            "model": {
              "format": "utc",
              "granularity": "auto",
              "relative": "30d"
            },
            "displayCache": {
              "name": "UTC Time",
              "value": "Past 30 days"
            },
            "filteredPartIds": [
              "StartboardPart-MonitorChartPart-55acd30a-365e-4dcb-b593-73c7e22c3fc1",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c3747",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c39fc",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c3236",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c3238",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c323a",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c323c",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c323e",
              "StartboardPart-LogsDashboardPart-55acd30a-365e-4dcb-b593-73c7e22c3773"
            ]
          }
        }
      }
    }
  }
}
