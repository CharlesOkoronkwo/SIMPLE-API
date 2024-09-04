terraform {
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = "2.32.0"
    }
}
}

provider "kubernetes" {
  # Configuration options
    config_path    = "~/.kube/config"
    config_context = "gke_simple-api-434410_us-central1_simple-api"
}