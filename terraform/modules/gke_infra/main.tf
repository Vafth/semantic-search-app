# —— Google Services ———————————————————————————————————————————————————————————

resource "google_project_service" "apis" {
  for_each = local.gcp_services
  service  = each.value
  disable_on_destroy = false
}


# —— VPC ———————————————————————————————————————————————————————————————————————

resource "google_compute_network" "vpc" {
  name = local.full_network_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = local.full_subnet_name
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}


# —— GKE Cluster ———————————————————————————————————————————————————————————————

resource "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.zone

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name
  
  remove_default_node_pool = true
  initial_node_count       = var.init_node_count
  
  deletion_protection = false
  resource_labels     = local.common_labels

  depends_on = [google_project_service.apis]
}


# —— Node Pool —————————————————————————————————————————————————————————————————

resource "google_container_node_pool" "nodes" {
  name       = local.full_node_pool_name
  location   = var.zone
  cluster    = google_container_cluster.cluster.name
  node_count = var.init_node_count

  node_config {
    machine_type = var.machine_type
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }
}


# —— Namespace —————————————————————————————————————————————————————————————————

resource "kubernetes_namespace" "semantic_search" {
  metadata {
    name = local.namespace
  }
}


# —— Static IP —————————————————————————————————————————————————————————————————

resource "google_compute_address" "public_ip" {
  name   = local.full_ip_name
  region = var.region

  depends_on = [ google_container_cluster.cluster ]
}