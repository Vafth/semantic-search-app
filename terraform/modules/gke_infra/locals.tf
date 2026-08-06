# —— Locals ————————————————————————————————————————————————————————————————————

locals {
  resource_prefix = var.cluster_name

  common_labels = {}
  
  gcp_services = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
  ])
  
  full_network_name   = "${local.resource_prefix}-vpc"
  full_subnet_name    = "${local.resource_prefix}-subnet"
  full_node_pool_name = "${local.resource_prefix}-pool"
  full_ip_name        = "${local.resource_prefix}-ip"
  namespace           = "${local.resource_prefix}-ns"
}