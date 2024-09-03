#resource "google_compute_router" "nat_router" {
#  name    = "nat-router"
#  network = google_compute_network.vpc_network.name
#  region  = var.region
#}

resource "google_compute_router_nat" "nat_gw" {
  name                                = "nat-config"
  router                              = google_compute_router.nat_router.name
  region                              = var.region
  nat_ip_allocate_option              = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat  = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  depends_on = [ google_project_service.compute ]
}