terraform {
  backend "gcs" {
    bucket  = "tfstateaccount"
    prefix  = "terraform/state"
  }
}


module "gke" {
    source = "./modules/gke"
}



resource "kubernetes_namespace_v1" "simple_api" {
  metadata {
    name = "simple-api"
  }
}



resource "kubernetes_deployment_v1" "api_deployment" {
  metadata {
    name      = "simple-api"
    namespace = "simple-api"
    labels = {
      app = "simple-api"
    }
  }
  depends_on = [kubernetes_namespace_v1.simple_api]


  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "simple-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "simple-api"
        }
      }

      spec {
        container {
          image = "taylorbree/simple-api:latest"
          name  = "simple-api"

          port {
            container_port = 8080
          }
        }
      }
    }
  }
}
          
resource "kubernetes_service" "api_service" {
  depends_on = [kubernetes_deployment_v1.api_deployment]
  metadata {
    name      = "simple-api-service"
    namespace = "simple-api"
    labels = {
      app = "simple-api"
    }
  }

  spec {
    selector = {
      app = "simple-api"
    }

    port {
      port        = 80
      target_port = 8080
    }

    type = "LoadBalancer"
  }
}

