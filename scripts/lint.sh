#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Ensure lint tools are installed (same pinned versions as CI)
if ! command -v flake8 &>/dev/null || ! command -v yamllint &>/dev/null || ! command -v ansible-lint &>/dev/null; then
    echo "Installing lint tools from requirements-lint.txt..."
    pip install -r requirements-lint.txt
fi

echo "=== Python lint (flake8) ==="
flake8 django_app/ --max-line-length 120 --exclude venv,migrations

echo "=== YAML lint ==="
yamllint -d relaxed ansible/ monitoring/

echo "=== Ansible lint ==="
ansible-lint ansible/playbooks/site.yml

echo "=== Terraform format ==="
cd terraform && terraform fmt -check && cd "$REPO_ROOT"

echo "=== Terraform validate ==="
cd terraform && terraform init -backend=false -input=false >/dev/null 2>&1 && terraform validate && cd "$REPO_ROOT"

echo ""
echo "All lints passed!"
