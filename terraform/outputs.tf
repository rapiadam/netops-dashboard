output "prometheus_url" {
  value = "http://localhost:${var.prometheus_port}"
}

output "grafana_url" {
  value = "http://localhost:${var.grafana_port}"
}

output "grafana_credentials" {
  value     = "admin / ${var.grafana_admin_password}"
  sensitive = true
}

output "network_name" {
  value = docker_network.netops.name
}

output "database_url" {
  value     = "postgres://netops:${var.postgres_password}@localhost:${var.postgres_port}/${var.postgres_db}"
  sensitive = true
}
