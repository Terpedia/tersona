# Cloud NAT for outbound internet access from VMs without external IPs

resource "google_compute_router" "nat_router" {
  name    = "librechat-nat-router"
  region  = var.region
  network = "default"
}

resource "google_compute_router_nat" "nat" {
  name                               = "librechat-nat"
  router                             = google_compute_router.nat_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
