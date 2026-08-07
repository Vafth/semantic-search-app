# —— GKE Infrastructure ————————————————————————————————————————————————————————

module "gke" {
  source = "./modules/gke_infra"

  project         = var.project
  region          = var.region
  zone            = var.zone
  cluster_name    = var.cluster_name
  subnet_cidr     = var.subnet_cidr
  machine_type    = var.machine_type
  init_node_count = var.init_node_count

  # secrets
  postgres_db       = var.postgres_db
  postgres_user     = var.postgres_user
  postgres_password = var.postgres_password
  secret_key        = var.secret_key
  OWNER_PASSWORD    = var.OWNER_PASSWORD
  OWNER_USERNAME    = var.OWNER_USERNAME

}

# —— Helm Chart ————————————————————————————————————————————————————————————————

module "helm" {
  source = "./modules/helm"

  release_name     = var.release_name
  chart_path       = var.chart_path
  namespace        = module.gke.namespace
  load_balancer_ip = module.gke.public_ip

  depends_on = [module.gke]
}