output "network_self_link" {
  value = google_compute_network.vpc_network.self_link
  description = "The self link of the VPC network"
}

output "subnetwork_self_link" {
  value       = google_compute_subnetwork.private.self_link
  description = "The self link of the private subnetwork"
}