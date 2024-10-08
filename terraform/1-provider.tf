# terraform {
#   required_providers {
#     kubernetes = {
#       source = "hashicorp/kubernetes"
#       version = "2.32.0"
#     }
# }
# }

# provider "kubernetes" {
#   # Configuration options
#     config_path    = "~/.kube/config"
#     config_context = "minikube"
# }

terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "6.1.0"
    }
  }
}
provider "google" {
  project     = "simple-api-434410"
  region      = "us-central1"
}

