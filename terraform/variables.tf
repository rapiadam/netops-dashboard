variable "project_name" {
  description = "Projekt prefix for all resources"
  type        = string
  default     = "netops"
}

variable "prometheus_port" {
  description = "External port for Prometheus"
  type        = number
  default     = 9090
}

variable "grafana_port" {
  description = "External port for Grafana"
  type        = number
  default     = 3000
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "postgres_port" {
  description = "External port for PostgreSQL"
  type        = number
  default     = 5432
}

variable "postgres_db" {
  description = "PostgreSQL database name"
  type        = string
  default     = "netops"
}
