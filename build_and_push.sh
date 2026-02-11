#!/usr/bin/env bash
# Build all NCI DSA DeID images and push to Docker Hub.
# Run from repo root. Colleagues can then use: docker compose pull && docker compose up -d
# (from devops/nci-dsa-deid) with no local builds.
#
# Prereq: docker login (so you can push to your namespace).

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

# Docker Hub namespace (e.g. dagutman). Override with env if needed.
DOCKER_NAMESPACE="${DOCKER_NAMESPACE:-dagutman}"

echo "Using Docker namespace: $DOCKER_NAMESPACE"
echo "Building and pushing from: $REPO_ROOT"

# 1) Girder / main DSA image (used by girder service)
echo "--- Building $DOCKER_NAMESPACE/nci-dsa-deid:latest ---"
docker build -f devops/nci-dsa-deid/Dockerfile -t "$DOCKER_NAMESPACE/nci-dsa-deid:latest" .
docker push "$DOCKER_NAMESPACE/nci-dsa-deid:latest"

# 2) Nginx with our config (routing for /dsa, /deid, etc.)
echo "--- Building $DOCKER_NAMESPACE/nci-dsa-deid-nginx:latest ---"
docker build -f services/nginx/Dockerfile -t "$DOCKER_NAMESPACE/nci-dsa-deid-nginx:latest" services/nginx
docker push "$DOCKER_NAMESPACE/nci-dsa-deid-nginx:latest"

# 3) Dash DeID app (optional; not in current compose but in original build script)
echo "--- Building $DOCKER_NAMESPACE/dashncidsadeidapp:latest ---"
docker build --platform=linux/amd64 -f services/dashdeid/Dockerfile -t "$DOCKER_NAMESPACE/dashncidsadeidapp:latest" services/dashdeid
docker push "$DOCKER_NAMESPACE/dashncidsadeidapp:latest"

# 4) React DeID (Vite app; used by reactdeid service)
echo "--- Building $DOCKER_NAMESPACE/reactdeid:latest ---"
docker build -f services/reactdeid/Dockerfile -t "$DOCKER_NAMESPACE/reactdeid:latest" services/reactdeid
docker push "$DOCKER_NAMESPACE/reactdeid:latest"

# 5) Node API (used by node service)
echo "--- Building $DOCKER_NAMESPACE/bdsa-node:0.0.1 ---"
docker build -f services/node/Dockerfile -t "$DOCKER_NAMESPACE/bdsa-node:0.0.1" services/node
docker push "$DOCKER_NAMESPACE/bdsa-node:0.0.1"

echo "Done. Images pushed to $DOCKER_NAMESPACE/*"
echo "Colleagues: cd devops/nci-dsa-deid && docker compose pull && ./start_dsadeid.sh  # (or set DSA_USER and run compose up -d)"
