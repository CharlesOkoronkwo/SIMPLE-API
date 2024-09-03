#resource "google_service_account" "default" {
 # account_id   = "simple-api-svc-acct"


resource "google_container_cluster" "primary" {
  name               = "simple-api"
  initial_node_count = 1
  network = google_compute_network.vpc_network.self_link
  subnetwork = google_compute_subnetwork.private_new.self_link
  logging_service = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  deletion_protection = false

  node_locations = [
    "us-central1-c",
  ]

  node_config {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = "simple-api-svc-acct@simple-api-434410.iam.gserviceaccount.com"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}