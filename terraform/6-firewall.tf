resource "google_compute_firewall" "allow-http-traffic" {
  name    = "allow-http-traffic"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["80", "8080"]
  }

  source_ranges = ["0.0.0.0/0"]
}
