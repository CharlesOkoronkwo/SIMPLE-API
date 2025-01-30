resource "google_container_cluster" "primary" {
  name               = "simple-api"
  initial_node_count = 1
  network = google_compute_network.vpc_network.self_link
  subnetwork = google_compute_subnetwork.private.self_link
  logging_service = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  deletion_protection = false

  node_locations = [
    "us-central1-c",
  ]

  node_config {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = "github-wif@simple-api-434410.iam.gserviceaccount.com"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

resource "google_project_service" "compute" {
    service = "compute.googleapis.com"
  }
resource "google_project_service" "container" {
    service = "container.googleapis.com"
  }
resource "google_compute_network" "vpc_network" {
  project                 = "simple-api-434410"
  name                    = "vpc-network"
  auto_create_subnetworks = false
  mtu                     = 1460

  depends_on = [
    google_project_service.compute,
    google_project_service.container
  ]
}
resource "google_compute_subnetwork" "private" {
  name          = "private-new"
  ip_cidr_range = "10.3.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id
  secondary_ip_range {
    range_name    = "tf-test-secondary-range-update1"
    ip_cidr_range = "192.168.10.0/24"
  }
}

# resource "google_compute_network" "custom-test" {
#   name                    = "test-network"
#   auto_create_subnetworks = false 
# }

resource "google_compute_router" "nat_router" {
  name    = "nat-router"
  network = google_compute_network.vpc_network.name
  region  = var.region
}

resource "google_compute_router_nat" "nat_gw" {
  name                                = "nat-config"
  router                              = google_compute_router.nat_router.name
  region                              = var.region
  nat_ip_allocate_option              = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat  = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  depends_on = [ google_project_service.compute ]
}

resource "google_compute_router" "router" {
  name = "router"
  region = var.region
  network = google_compute_network.vpc_network.id
}
resource "google_compute_firewall" "allow-http-traffic" {
  name    = "allow-http-traffic"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["80", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
}

