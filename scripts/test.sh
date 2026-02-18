#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

IMAGE="netops-test"
NEED_BUILD=false
DEBUG_MODE=false

# Check if test image exists
if ! docker image inspect "$IMAGE" &>/dev/null; then
    NEED_BUILD=true
fi

# Parse flags
while [ $# -gt 0 ]; do
    case "$1" in
        --build)  NEED_BUILD=true; shift ;;
        --debug)  DEBUG_MODE=true; shift ;;
        *)        break ;;
    esac
done

if [ "$NEED_BUILD" = true ]; then
    echo "=== Building test image ==="
    docker build -t "$IMAGE" -f - django_app/ <<'DOCKERFILE'
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV SECRET_KEY=test-secret-key
ENV DEBUG=true
ENV ALLOWED_HOSTS=localhost,127.0.0.1
RUN python -c "import django; django.setup()" 2>/dev/null || true
DOCKERFILE
    echo ""
fi

DOCKER_ARGS=(
    --rm
    -v "$REPO_ROOT/django_app:/app"
    -e DJANGO_SETTINGS_MODULE=config.settings
    -e SECRET_KEY=test-secret-key
    -e DEBUG=true
    -e ALLOWED_HOSTS=localhost,127.0.0.1
)

if [ "$DEBUG_MODE" = true ]; then
    echo "=== Debug shell (use breakpoint() in tests, run: pytest -s -k 'test_name') ==="
    docker run -it "${DOCKER_ARGS[@]}" "$IMAGE" bash
else
    echo "=== Running tests ==="
    docker run "${DOCKER_ARGS[@]}" "$IMAGE" \
        sh -c "python manage.py migrate --noinput -v0 2>/dev/null && python -m pytest -v --tb=short --cov=monitor --cov-report=term-missing $*"
fi
