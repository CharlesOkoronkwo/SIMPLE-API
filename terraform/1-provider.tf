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


provider "google" {
  project = "simple-api-434410"
  region  = "us-central1"
  impersonate_service_account = "github-wif@simple-api-434410.iam.gserviceaccount.com"
}
