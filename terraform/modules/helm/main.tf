# —— Helm ——————————————————————————————————————————————————————————————————————

resource "helm_release" "helm" {
  name      = var.release_name
  chart     = var.chart_path
  namespace = var.namespace

  
  set {
    name = "service.loadBalancerIP"
    value = var.load_balancer_ip
  }

  values = var.values_file != null ? [file(var.values_file)] : []
}