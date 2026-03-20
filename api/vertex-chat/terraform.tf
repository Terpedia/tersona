# Terraform configuration for TerpeneQueen Cloud Run API

terraform {
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
  default     = "terpedia-489015"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_account_email" {
  description = "Service account email for Cloud Run (with Vertex AI, Speech, TTS permissions)"
  type        = string
  default     = "" # Will use default compute service account if empty
}

# Cloud Run service
resource "google_cloud_run_v2_service" "terpenequeen_api" {
  name     = "terpenequeen-api"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "gcr.io/${var.project_id}/terpenequeen-api:latest"

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_LOCATION"
        value = var.region
      }

      env {
        name  = "DEFAULT_TTS_VOICE"
        value = "en-US-Neural2-F"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }

    service_account = var.service_account_email != "" ? var.service_account_email : null

    timeout_seconds = 300

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  traffic {
    percent = 100
    latest  = true
  }
}

# Allow unauthenticated access
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_v2_service.terpenequeen_api.name
  location = google_cloud_run_v2_service.terpenequeen_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.terpenequeen_api.uri
}

output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_v2_service.terpenequeen_api.name
}
