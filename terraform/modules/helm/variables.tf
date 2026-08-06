# —— Helm ——————————————————————————————————————————————————————————————————————

variable "release_name" {
  type        = string
  description = "Helm release name"
}

variable "chart_path" {
  type        = string
  description = "Path to the Helm chart directory"
} 


# —— GKE ———————————————————————————————————————————————————————————————————————

variable "load_balancer_ip" {
  type        = string
  description = "Static IP for the LoadBalancer service"
  default     = ""
}

variable "values_file" {
  type        = string
  description = "Optional path to a values.yaml file"
  default     = null
}

variable "namespace" {
  type        = string
  description = "Namespace for a Helm Chart deploy"
  default     = "default"
}