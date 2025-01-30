
terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.1.0"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "2.32.0"
    }
  }
}
provider "google" {
  project     = "simple-api-434410"
  region      = var.region
}


provider "kubernetes" {
  host                   = "https://${module.gke.cluster_endpoint}"
  token                  = data.google_client_config.default.access_token
  # cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
  cluster_ca_certificate = module.gke.cluster_ca_certificate

}

data "google_client_config" "default" {}

# data "google_container_cluster" "my_cluster" {
#   name     = "simple-api"
#   location = "us-central1"
#   project  = "simple-api-434410"
# }

