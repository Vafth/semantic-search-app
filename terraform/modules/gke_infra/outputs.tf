output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.cluster.endpoint
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate (base64 encoded)"
  value       = google_container_cluster.cluster.master_auth[0].cluster_ca_certificate
}

output "public_ip" {
  description = "Reserved static IP for Helm Chart LoadBalancer"
  value = google_compute_address.public_ip.address
}

output "namespace" {
  description = "Namespace where the release is deployed"
  value       = local.namespace
}