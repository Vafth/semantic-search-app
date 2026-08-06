# —— Providers —————————————————————————————————————————————————————————————————

data "google_client_config" "default" {}

provider "google" {
  project = var.project
  region  = var.region
}

provider "helm" {
  kubernetes {
    host  = "https://${module.gke.cluster_endpoint}"
    token = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.gke.cluster_ca_certificate) 
  }
}

provider "kubernetes" {
  host                   = "https://${module.gke.cluster_endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.cluster_ca_certificate)
}