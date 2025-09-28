# Google Cloud Run deployment with Terraform
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (staging/production)"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "sharepoint_endpoint" {
  description = "SharePoint API endpoint"
  type        = string
  sensitive   = true
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Cloud Run service
resource "google_cloud_run_service" "netanya_incident_service" {
  name     = "netanya-incident-service-${var.environment}"
  location = var.region

  template {
    metadata {
      annotations = {
        "run.googleapis.com/memory"        = var.environment == "production" ? "1Gi" : "512Mi"
        "run.googleapis.com/cpu"           = var.environment == "production" ? "2" : "1"
        "run.googleapis.com/min-instances" = var.environment == "production" ? "1" : "0"
        "run.googleapis.com/max-instances" = var.environment == "production" ? "100" : "10"
      }
    }

    spec {
      container_concurrency = 80
      timeout_seconds      = 300

      containers {
        image = "ghcr.io/motis10/incident-service:${var.image_tag}"
        
        ports {
          container_port = 8000
        }

        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "DEBUG_MODE"
          value = var.environment == "production" ? "false" : "true"
        }

        env {
          name  = "LOG_LEVEL"
          value = var.environment == "production" ? "INFO" : "DEBUG"
        }

        env {
          name  = "PORT"
          value = "8000"
        }

        env {
          name = "SHAREPOINT_ENDPOINT"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret_version.sharepoint_endpoint.secret
              key  = google_secret_manager_secret_version.sharepoint_endpoint.version
            }
          }
        }

        resources {
          limits = {
            memory = var.environment == "production" ? "1Gi" : "512Mi"
            cpu    = var.environment == "production" ? "2" : "1"
          }
        }

        liveness_probe {
          http_get {
            path = "/health/live"
            port = 8000
          }
          initial_delay_seconds = 30
          period_seconds       = 30
          timeout_seconds      = 5
          failure_threshold    = 3
        }

        readiness_probe {
          http_get {
            path = "/health/ready"
            port = 8000
          }
          initial_delay_seconds = 10
          period_seconds       = 10
          timeout_seconds      = 5
          failure_threshold    = 3
        }

        startup_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 15
          period_seconds       = 5
          timeout_seconds      = 5
          failure_threshold    = 15
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# IAM policy for public access
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_service.netanya_incident_service.location
  project  = google_cloud_run_service.netanya_incident_service.project
  service  = google_cloud_run_service.netanya_incident_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Secret Manager for SharePoint endpoint
resource "google_secret_manager_secret" "sharepoint_endpoint" {
  secret_id = "sharepoint-endpoint-${var.environment}"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "sharepoint_endpoint" {
  secret      = google_secret_manager_secret.sharepoint_endpoint.id
  secret_data = var.sharepoint_endpoint
}

# Outputs
output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.netanya_incident_service.status[0].url
}

output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_service.netanya_incident_service.name
}
