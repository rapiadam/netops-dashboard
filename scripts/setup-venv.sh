#!/usr/bin/env bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$REPO_ROOT/django_app/venv"

# Find best available Python
PYTHON=""
for candidate in python3.13 python3.12 python3; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: No Python 3.12+ found. Install Python 3.12 or 3.13."
    exit 1
fi

echo "Using: $PYTHON ($($PYTHON --version))"

if [ ! -d "$VENV_DIR" ] || [ "$1" = "--force" ]; then
    echo "Creating venv at $VENV_DIR..."
    $PYTHON -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$REPO_ROOT/django_app/requirements-dev.txt"

echo ""
echo "Done! To activate:"
echo "  source django_app/venv/bin/activate"
echo ""
echo "PyCharm setup:"
echo "  1. Settings > Project > Python Interpreter"
echo "  2. Add Interpreter > Existing > $VENV_DIR/bin/python"
echo "  3. Set env vars in Run Configuration:"
echo "     SECRET_KEY=test-secret-key"
echo "     DEBUG=true"
echo "     ALLOWED_HOSTS=localhost,127.0.0.1"
