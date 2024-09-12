terraform {
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "2.32.0"
    }
}
}

provider "kubernetes" {
  host                   = "https://${data.google_container_cluster.my_cluster.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(data.google_container_cluster.my_cluster.master_auth[0].cluster_ca_certificate)
}

data "google_client_config" "default" {}

data "google_container_cluster" "my_cluster" {
  name     = "simple-api"
  location = "us-central1"
  project  = "simple-api-434410"
}

