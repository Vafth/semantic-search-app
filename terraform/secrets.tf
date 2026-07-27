# postgres-secret.tf
resource "kubernetes_secret" "postgres_secret" {
  metadata {
    name      = "postgres-secret"
    namespace = kubernetes_namespace.semantic_search.metadata[0].name
  }
  data = {
    POSTGRES_DB       = var.postgres_db
    POSTGRES_USER     = var.postgres_user
    POSTGRES_PASSWORD = var.postgres_password
    POSTGRES_URL      = "postgresql+asyncpg://${var.postgres_user}:${var.postgres_password}@postgres:5432/${var.postgres_db}"
  }
}

# auth-secret.tf
resource "kubernetes_secret" "auth_secret" {
  metadata {
    name      = "auth-secret"
    namespace = kubernetes_namespace.semantic_search.metadata[0].name
  }
  data = {
    SECRET_KEY     = var.secret_key
    OWNER_USERNAME = var.OWNER_USERNAME
    OWNER_PASSWORD = var.OWNER_PASSWORD
  }
}