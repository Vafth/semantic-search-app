variable "postgres_db" {
  description = "PostgreSQL database name"
  default     = "project_db"
}

variable "postgres_user" {
  description = "PostgreSQL user"
  default     = "admin"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  sensitive   = true
}

variable "secret_key" {
  description = "Secret Key for AUTH"
  sensitive   = true
}

variable "OWNER_PASSWORD" {
  description = "Owner user password"
  sensitive   = true
}

variable "OWNER_USERNAME" {
  description = "Owner user username"
  sensitive   = true
}