output "network_self_link" {
  value = google_compute_network.vpc_network.self_link
  description = "The self link of the VPC network"
}

output "subnetwork_self_link" {
  value       = google_compute_subnetwork.private.self_link
  description = "The self link of the private subnetwork"
}

output "cluster_endpoint" {
  value = google_container_cluster.primary.endpoint
  description = "Endpoint for the GKE cluster"
}

output "cluster_ca_certificate" {
  value = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
  description = "CA certificate for the GKE cluster"
}