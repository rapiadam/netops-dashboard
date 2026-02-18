terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ---- Network ----

resource "docker_network" "netops" {
  name = "${var.project_name}_network"
}

# ---- Volumes (persistent storage) ----

resource "docker_volume" "prometheus_data" {
  name = "${var.project_name}_prometheus_data"
}

resource "docker_volume" "grafana_data" {
  name = "${var.project_name}_grafana_data"
}

resource "docker_volume" "postgres_data" {
  name = "${var.project_name}_postgres_data"
}

# ---- Images ----

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

resource "docker_image" "postgres" {
  name         = "postgres:16-alpine"
  keep_locally = true
}

# ---- PostgreSQL ----

resource "docker_container" "postgres" {
  name  = "${var.project_name}_postgres"
  image = docker_image.postgres.image_id

  ports {
    internal = 5432
    external = var.postgres_port
  }

  networks_advanced {
    name = docker_network.netops.id
  }

  env = [
    "POSTGRES_DB=${var.postgres_db}",
    "POSTGRES_USER=netops",
    "POSTGRES_PASSWORD=${var.postgres_password}",
  ]

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  restart = "unless-stopped"

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U netops -d ${var.postgres_db}"]
    interval = "10s"
    timeout  = "5s"
    retries  = 5
  }
}

# ---- Prometheus ----

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

  volumes {
    volume_name    = docker_volume.prometheus_data.name
    container_path = "/prometheus"
  }

  restart = "unless-stopped"
}

# ---- Grafana ----

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

  volumes {
    volume_name    = docker_volume.grafana_data.name
    container_path = "/var/lib/grafana"
  }

  restart = "unless-stopped"
}

# ---- Node Exporter ----

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
