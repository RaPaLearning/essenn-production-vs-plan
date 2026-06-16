#!/usr/bin/env -S uv run bash
set -e  # Exit on any error

echo "🎨 Format code with ruff"
ruff format

echo "🧩 Detect duplicates"
if command -v npx &> /dev/null; then
    npx jscpd .
else
    echo "⚠️  ✗ npx not found, skipping jscpd duplicate detection"
    read -p "Do you want to proceed anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔍 Lint python code"
ruff check .

echo "🧠 Check types, unreachable code, uninitialized variables"
pyright 

echo "🦅 Detect dead code"
vulture --exclude .venv . --min-confidence 100

echo "🛡️ Guard against unsecure code patterns"
bandit --exclude ./.venv,./.ruff_cache/ -r .

echo "🔐 Guard against secrets in code"
git ls-files -z | xargs -0 detect-secrets-hook --baseline .secrets.baseline

echo "🧪 Run tests with coverage"
rm -rf .coverage
coverage run -p -m unittest discover -s tests
coverage combine
coverage report --fail-under=100
coverage html

echo "📦 Audit dependencies"
pip-audit .
