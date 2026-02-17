terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  # macOS Docker Desktop – default unix socket
  # Linux: unix:///var/run/docker.sock
  # Windows: npipe:////.//pipe//docker_engine
}

# ---- variables ----

variable "project_name" {
  description = "Projekt prefix"
  type        = string
  default     = "netops"
}

variable "prometheus_port" {
  type    = number
  default = 9090
}

variable "grafana_port" {
  type    = number
  default = 3000
}

variable "grafana_admin_password" {
  type      = string
  default   = "netops123"
  sensitive = true
}

resource "docker_network" "netops" {
  name = "${var.project_name}_network"
}

resource "docker_image" "prometheus" {
  name         = "prom/prometheus:v2.51.0"
  keep_locally = true
}

resource "docker_image" "grafana" {
  name         = "grafana/grafana:10.4.0"
  keep_locally = true
}

resource "docker_image" "node_exporter" {
  name         = "prom/node-exporter:v1.7.0"
  keep_locally = true
}

resource "docker_container" "prometheus" {
  name  = "${var.project_name}_prometheus"
  image = docker_image.prometheus.image_id

  ports {
    internal = 9090
    external = var.prometheus_port
  }

  networks_advanced {
    name = docker_network.netops.id
  }
  
  volumes {
    host_path      = abspath("${path.module}/../monitoring/prometheus.yml")
    container_path = "/etc/prometheus/prometheus.yml"
    read_only      = true
  }

  restart = "unless-stopped"
}

resource "docker_container" "grafana" {
  name  = "${var.project_name}_grafana"
  image = docker_image.grafana.image_id

  ports {
    internal = 3000
    external = var.grafana_port
  }

  networks_advanced {
    name = docker_network.netops.id
  }

  env = [
    "GF_SECURITY_ADMIN_PASSWORD=${var.grafana_admin_password}",
    "GF_USERS_ALLOW_SIGN_UP=false",
  ]

  restart = "unless-stopped"
}

resource "docker_container" "node_exporter" {
  name  = "${var.project_name}_node_exporter"
  image = docker_image.node_exporter.image_id

  ports {
    internal = 9100
    external = 9100
  }

  networks_advanced {
    name = docker_network.netops.id
  }

  restart = "unless-stopped"
}

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