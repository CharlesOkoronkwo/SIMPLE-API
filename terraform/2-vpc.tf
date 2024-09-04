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
