# Optional: HTTPS load balancer with Google-managed certificate for chat.tersona.terpedia.com
# Use this if you want SSL at the edge and a single public IP for the LB instead of exposing the VM directly.

# Reserve a static IP for the load balancer
resource "google_compute_global_address" "lb_ip" {
  name = "librechat-lb-ip"
}

# Backend: instance group containing the LibreChat VM (simplified: single instance)
# For production you might use an instance group with multiple instances.
resource "google_compute_instance_group" "librechat" {
  name        = "librechat-instance-group"
  zone        = google_compute_instance.librechat.zone
  description = "LibreChat instance group"

  instances = [
    google_compute_instance.librechat.self_link,
  ]

  named_port {
    name = "http"
    port = 3080
  }
}

resource "google_compute_backend_service" "librechat" {
  name                  = "librechat-backend"
  port_name             = "http"
  protocol              = "HTTP"
  timeout_sec           = 30
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_instance_group.librechat.id
  }

  health_checks = [google_compute_health_check.librechat.id]
}

resource "google_compute_health_check" "librechat" {
  name = "librechat-health"

  http_health_check {
    port         = 3080
    request_path = "/"
  }
}

# Google-managed SSL certificate (DNS must point to lb_ip before cert can be issued)
resource "google_compute_managed_ssl_certificate" "librechat" {
  name = "librechat-ssl-cert"

  managed {
    domains = [var.domain]
  }
}

# URL map and HTTPS proxy
resource "google_compute_url_map" "librechat" {
  name            = "librechat-url-map"
  default_service = google_compute_backend_service.librechat.id
}

resource "google_compute_target_https_proxy" "librechat" {
  name             = "librechat-https-proxy"
  url_map          = google_compute_url_map.librechat.id
  ssl_certificates = [google_compute_managed_ssl_certificate.librechat.id]
}

resource "google_compute_global_forwarding_rule" "librechat_https" {
  name                  = "librechat-https-rule"
  ip_protocol           = "TCP"
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  target                = google_compute_target_https_proxy.librechat.id
  ip_address            = google_compute_global_address.lb_ip.id
}

# Optional: HTTP -> HTTPS redirect
resource "google_compute_url_map" "http_redirect" {
  name = "librechat-http-redirect"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query           = false
  }
}

resource "google_compute_target_http_proxy" "librechat_http" {
  name    = "librechat-http-proxy"
  url_map = google_compute_url_map.http_redirect.id
}

resource "google_compute_global_forwarding_rule" "librechat_http" {
  name                  = "librechat-http-rule"
  ip_protocol           = "TCP"
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  target                = google_compute_target_http_proxy.librechat_http.id
  ip_address            = google_compute_global_address.lb_ip.id
}

output "lb_ip" {
  value       = google_compute_global_address.lb_ip.address
  description = "Create a DNS A record for chat.tersona.terpedia.com pointing to this IP"
}
