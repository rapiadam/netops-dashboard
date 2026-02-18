# NetOps Dashboard

Network operations monitoring dashboard with Django REST API, Prometheus metrics, and Grafana visualization.

## Project Structure

```
netops-dashboard/
├── django_app/                  # Django application
│   ├── config/                  # Django settings, URLs, WSGI
│   │   ├── settings.py          # Main configuration (env-based)
│   │   ├── urls.py              # API routing (versioned)
│   │   └── wsgi.py              # WSGI entry point
│   ├── monitor/                 # Core monitoring app
│   │   ├── models.py            # ServiceTarget, CheckResult
│   │   ├── views.py             # DRF API views (auth-protected)
│   │   ├── serializers.py       # DRF serializers
│   │   ├── services.py          # ServiceChecker (HTTP probe logic)
│   │   ├── metrics.py           # Prometheus metrics + /metrics endpoint
│   │   ├── admin.py             # Django admin registration
│   │   ├── tests.py             # Unit + integration tests
│   │   └── management/commands/ # CLI commands (run_checks, ensure_superuser)
│   ├── Dockerfile               # Production image (gunicorn, non-root)
│   ├── .dockerignore
│   ├── requirements.txt         # Production dependencies
│   ├── requirements-dev.txt     # Dev/test dependencies
│   └── pytest.ini               # Pytest configuration
├── ansible/                     # Deployment automation
│   ├── playbooks/site.yml       # Main playbook
│   ├── inventory/hosts.yml      # Inventory (localhost)
│   ├── roles/
│   │   ├── django_app/          # Django build + deploy role
│   │   └── monitoring/          # Grafana datasource setup role
│   ├── vault/
│   │   ├── secrets.yml          # Encrypted secrets (ansible-vault)
│   │   └── secrets.yml.example  # Template for creating vault
│   └── ansible.cfg
├── terraform/                   # Infrastructure as Code
│   ├── main.tf                  # Docker resources (PostgreSQL, Prometheus, Grafana, Node Exporter)
│   ├── variables.tf             # Input variables
│   ├── outputs.tf               # Output values
│   └── terraform.tfvars.example # Example variable values
├── monitoring/
│   ├── prometheus.yml           # Prometheus scrape configuration
│   └── alert_rules.yml          # Alerting rules
├── scripts/
│   └── lint.sh                  # Run all linters locally
├── docker-compose.yml           # Local development (alternative to Terraform)
├── requirements-lint.txt        # Pinned lint tool versions (shared with CI)
└── .github/workflows/
    ├── ci.yml                   # Lint, test, build, security scan
    └── deploy.yml               # Ansible deployment (manual trigger)
```

## Prerequisites

- Docker Desktop
- Terraform >= 1.0
- Python 3.12+ (for local lint/test without Docker)

## Local Setup

### Option A: Terraform (recommended, matches production)

**1. Start infrastructure (PostgreSQL, Prometheus, Grafana, Node Exporter):**

```bash
cd terraform
terraform init
terraform apply \
  -var="grafana_admin_password=netops123" \
  -var="postgres_password=netopsdev"
```

**2. Build and run Django:**

```bash
cd django_app
docker build -t netops_django:latest .

docker run -d --name netops_django \
  --network netops_network \
  -p 8000:8000 \
  -e SECRET_KEY=local-dev-key-do-not-use-in-production \
  -e DEBUG=true \
  -e ALLOWED_HOSTS=localhost,127.0.0.1 \
  -e DATABASE_URL=postgres://netops:netopsdev@netops_postgres:5432/netops \
  netops_django:latest
```

**3. Run migrations and create superuser:**

```bash
docker exec netops_django python manage.py migrate --noinput
docker exec -e DJANGO_SUPERUSER_USERNAME=admin \
  -e DJANGO_SUPERUSER_EMAIL=admin@netops.local \
  -e DJANGO_SUPERUSER_PASSWORD=admin \
  netops_django python manage.py ensure_superuser
```

### Option B: Docker Compose (simpler, for development)

```bash
docker compose up -d
docker compose exec django python manage.py migrate --noinput
docker compose exec django python manage.py ensure_superuser
```

### Verify

| Service    | URL                          |
|------------|------------------------------|
| Django API | http://localhost:8000/health/ |
| Prometheus | http://localhost:9090         |
| Grafana    | http://localhost:3000         |

## API

All API endpoints (except `/health/`) require token authentication.

**Get a token:**

```bash
curl -X POST http://localhost:8000/api/v1/token/ \
  -d "username=admin&password=admin"
```

**Use the token:**

```bash
TOKEN="your-token-here"
curl -H "Authorization: Token $TOKEN" http://localhost:8000/api/v1/dashboard/
curl -X POST -H "Authorization: Token $TOKEN" http://localhost:8000/api/v1/check/
```

### Endpoints

| Method | Path                  | Auth     | Description               |
|--------|-----------------------|----------|---------------------------|
| GET    | `/health/`            | No       | Health check              |
| GET    | `/api/v1/dashboard/`  | Token    | Service summary + list    |
| POST   | `/api/v1/check/`      | Token    | Trigger health checks     |
| POST   | `/api/v1/token/`      | No       | Obtain auth token         |
| GET    | `/metrics`            | No       | Prometheus metrics        |
| GET    | `/admin/`             | Session  | Django admin              |

## Linting

Lint tools are pinned in `requirements-lint.txt` (same versions used in CI).

**Run all linters:**

```bash
./scripts/lint.sh
```

This runs:
- **flake8** - Python code style (max line length: 120)
- **yamllint** - YAML syntax validation
- **ansible-lint** - Ansible best practices
- **terraform fmt** - Terraform formatting check
- **terraform validate** - Terraform syntax validation

The script auto-installs missing lint tools from `requirements-lint.txt` on first run.

## Testing

**Run all tests (Docker-based, same Python 3.13 + deps as CI):**

```bash
./scripts/test.sh
```

This builds a test image once, then mounts your local source code as a volume. No local Python setup needed - only Docker.

| Command | Use case |
|---------|----------|
| `./scripts/test.sh` | Full suite with coverage (before commit) |
| `./scripts/test.sh -k "test_health"` | Run a specific test (TDD cycle) |
| `./scripts/test.sh -k "ServiceChecker"` | Run a test class |
| `./scripts/test.sh --build` | Rebuild image (after changing requirements) |
| `./scripts/test.sh --debug` | Interactive shell for debugging |

The image is built only on first run (or with `--build`). Subsequent runs use volume mounts, so local code changes are picked up instantly (~2s per run).

### Debugging tests

**Option A: Docker shell (no local Python needed)**

```bash
./scripts/test.sh --debug
```

This drops you into a bash shell inside the test container. Add `breakpoint()` anywhere in your code, then:

```bash
python manage.py migrate --noinput -v0
pytest -s -k "test_check_service_up"
```

The `-s` flag is required so `pdb` can work interactively.

**Option B: Local venv (for PyCharm / VS Code debugger)**

```bash
./scripts/setup-venv.sh
source django_app/venv/bin/activate
```

Then in PyCharm:
1. **Settings > Project > Python Interpreter** - select `django_app/venv/bin/python`
2. **Run/Debug Configuration > Environment variables:**
   ```
   SECRET_KEY=test-secret-key;DEBUG=true;ALLOWED_HOSTS=localhost,127.0.0.1
   ```
3. Set breakpoints in the gutter, right-click a test and **Debug**

Tests cover:
- Model validation and relationships
- ServiceChecker logic (mocked HTTP)
- API authentication enforcement
- Dashboard and check endpoints

## Monitoring

**Prometheus** scrapes metrics from Django (`/metrics`), Node Exporter, and itself.

**Alert rules** (in `monitoring/alert_rules.yml`):
- `ServiceDown` - monitored service unreachable for 2m
- `HighResponseTime` - p95 response time > 2s for 5m
- `DjangoDown` - Django not responding for 1m
- `HighCPUUsage` - CPU > 80% for 5m
- `HighMemoryUsage` - Memory > 85% for 5m
- `DiskSpaceLow` - Disk > 90% for 10m

## Deployment

### Ansible (with vault)

```bash
cd ansible/playbooks

# Dry run
ansible-playbook site.yml -i ../inventory/hosts.yml --ask-vault-pass --check --diff

# Deploy
ansible-playbook site.yml -i ../inventory/hosts.yml --ask-vault-pass
```

### CI/CD

- **CI** runs on push to `main`/`develop` and PRs: lint, test, Docker build, security scan, Terraform validate
- **Deploy** is manual via GitHub Actions workflow dispatch (staging/production)

## Teardown

**Terraform:**

```bash
cd terraform
terraform destroy \
  -var="grafana_admin_password=netops123" \
  -var="postgres_password=netopsdev"
docker rm -f netops_django
```

**Docker Compose:**

```bash
docker compose down -v
```
