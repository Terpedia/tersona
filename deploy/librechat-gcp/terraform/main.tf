# LibreChat on GCP — VPC, firewall, GCE instance
# Domain: chat.tersona.terpedia.com

variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP region"
}

variable "zone" {
  type        = string
  default     = "us-central1-a"
  description = "GCP zone for the VM"
}

variable "instance_name" {
  type        = string
  default     = "librechat"
  description = "Name of the GCE instance"
}

variable "machine_type" {
  type        = string
  default     = "e2-standard-4"
  description = "GCE machine type (4 vCPU, 16 GB RAM recommended for LibreChat + MongoDB + Meilisearch)"
}

variable "disk_size_gb" {
  type        = number
  default     = 100
  description = "Boot disk size in GB"
}

variable "domain" {
  type        = string
  default     = "chat.tersona.terpedia.com"
  description = "Domain for LibreChat"
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Optional: reserve a static IP for the VM (recommended so DNS doesn't change)
resource "google_compute_address" "librechat_static_ip" {
  name   = "librechat-ip"
  region = var.region
}

# Firewall: allow HTTP/HTTPS and LibreChat port (3080) from the world or from a load balancer only
resource "google_compute_firewall" "librechat_allow_http_https" {
  name    = "librechat-allow-http-https"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["librechat"]
}

resource "google_compute_firewall" "librechat_allow_app" {
  name    = "librechat-allow-app"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["3080"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["librechat"]
}

# GCE instance for LibreChat (Docker Compose runs here)
resource "google_compute_instance" "librechat" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["librechat"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"
    # No access_config block = no external IP
    # VM will only be accessible via the load balancer and Cloud IAP tunnel
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -e
    apt-get update
    apt-get install -y docker.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    # Create app dir; actual LibreChat files are deployed separately (e.g. via cloud-init or deploy script)
    mkdir -p /opt/librechat
    chown -R root:root /opt/librechat
  EOT
}

output "instance_name" {
  value = google_compute_instance.librechat.name
}

output "instance_zone" {
  value = google_compute_instance.librechat.zone
}

output "static_ip" {
  value       = google_compute_address.librechat_static_ip.address
  description = "Assign this IP to chat.tersona.terpedia.com (A record) or use behind a load balancer"
}

output "ssh_command" {
  value       = "gcloud compute ssh ${var.instance_name} --zone=${var.zone} --project=${var.project_id}"
  description = "SSH into the LibreChat VM"
}
