image := "ghcr.io/ryangreenup/sam-overlay-cli"
repo_root := justfile_directory()
flux_hook := env_var_or_default("FLUX_HOOK_URL", "")
doks_kubeconfig := env_var_or_default("DOKS_KUBECONFIG", env_var("HOME") / ".kube/do-cluster.conf")

# Computed once per `just` invocation, so build/scan/push all use the same tag.
# Matches the deploy-friendly format <unix-ts>-<sha8>.
sha := `git rev-parse --short=8 HEAD`
ts := `date +%s`
tag := ts + "-" + sha

default: check

check: fmt lint type test

# --- local development ---

tailwind-install:
    npm install

tailwind-build:
    npm run build:css

tailwind-watch:
    npm run watch:css

web:
    uv run dark-region-analysis-web

# --- image build and deploy ---

# Build the Flask web image, tagged :latest and :<ts>-<sha>.
build:
    cd "{{repo_root}}" && docker build -t "{{image}}:latest" -t "{{image}}:{{tag}}" .

# Trivy scan, fails on HIGH/CRITICAL. Requires: trivy
scan:
    trivy image --severity HIGH,CRITICAL --exit-code 1 "{{image}}:{{tag}}"

# Push both tags to GHCR. Requires: docker login ghcr.io -u ryangreenup
push:
    docker push "{{image}}:{{tag}}"
    docker push "{{image}}:latest"

# Run the compose stack with the locally built image.
compose-up:
    docker compose up --build

# Stop and remove the compose stack.
compose-down:
    docker compose down

# Nudge Flux to reconcile now instead of waiting for polling.
# Set FLUX_HOOK_URL when this app has a receiver. Set DOKS_KUBECONFIG to override kubeconfig.
reconcile:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -z "{{flux_hook}}" ]]; then
        echo "Set FLUX_HOOK_URL to reconcile {{image}}:{{tag}}" >&2
        exit 1
    fi
    token="$(KUBECONFIG='{{doks_kubeconfig}}' kubectl get secret -n flux-system webhook-token -o jsonpath='{.data.token}' | base64 -d)"
    body='{}'
    sig="$(printf '%s' "$body" | openssl dgst -sha256 -hmac "$token" | sed 's/^.* //')"
    curl -sS --fail-with-body -X POST "{{flux_hook}}" -H "Content-Type: application/json" -H "X-Signature: sha256=$sig" -d "$body"
    echo "reconciled {{image}}:{{tag}}"

# Full path with the Trivy gate: build -> scan -> push -> reconcile.
publish: build scan push reconcile

# Brief path, skips the scan: build -> push -> reconcile.
build-push: build push reconcile

# Build and push without reconciling Flux.
push-image: build push

fmt:
    uv run ruff format --check .

lint:
    uv run ruff check .

type:
    uv run pyright

test:
    uv run pytest
