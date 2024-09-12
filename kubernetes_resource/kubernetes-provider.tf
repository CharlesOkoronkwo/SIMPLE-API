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
  host  = "https://${data.google_container_cluster.cluster.endpoint}"
}
