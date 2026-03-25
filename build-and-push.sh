#!/bin/bash

# Script to build and push NCI-DSA-DEID Docker images
# 
# This script builds the custom images and optionally pushes them to Docker Hub
# so colleagues and IT can pull pre-built images without needing to build locally.
#
# Usage: 
#   ./build-and-push.sh              # Build locally only
#   ./build-and-push.sh --push       # Build and push to Docker Hub
#   ./build-and-push.sh --push --tag v1.2.3  # Build and push with custom tag
#
# For local development:
#   - Keep docker-compose.override.yml in place
#   - Run: docker-compose build (uses override file for local builds)
#
# For colleagues/IT:
#   - Remove or rename docker-compose.override.yml  
#   - Run: docker-compose pull (downloads from Docker Hub)

set -e

PUSH=false
TAG="latest"
BUILD_IN_COMPOSE_DIR=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--push] [--tag TAG]"
            exit 1
            ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$REPO_ROOT/devops/nci-dsa-deid"
echo "Repository root: $REPO_ROOT"
echo "Compose directory: $COMPOSE_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Docker Hub username (change if needed)
DOCKER_USER="${DOCKER_USER:-dagutman}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}NCI-DSA-DEID Docker Build Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Tag: ${BLUE}${TAG}${NC}"
echo -e "Push to registry: ${BLUE}${PUSH}${NC}"
echo ""

# Function to build an image
build_image() {
    local name=$1
    local context=$2
    local dockerfile=$3
    local image_name="${DOCKER_USER}/${name}:${TAG}"
    
    echo -e "${YELLOW}Building ${name}...${NC}"
    echo "  Context: $context"
    echo "  Image: $image_name"
    
    if [ -n "$dockerfile" ]; then
        docker build -t "$image_name" -f "$dockerfile" "$context"
    else
        docker build -t "$image_name" "$context"
    fi
    
    # Also tag as 'latest' if using a custom tag
    if [ "$TAG" != "latest" ]; then
        local latest_name="${DOCKER_USER}/${name}:latest"
        echo "  Also tagging as: $latest_name"
        docker tag "$image_name" "$latest_name"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully built ${image_name}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to build ${image_name}${NC}"
        return 1
    fi
}

# Function to push an image
push_image() {
    local name=$1
    local image_name="${DOCKER_USER}/${name}:${TAG}"
    
    echo -e "${YELLOW}Pushing ${image_name}...${NC}"
    docker push "$image_name"
    
    # Also push 'latest' if using a custom tag
    if [ "$TAG" != "latest" ]; then
        local latest_name="${DOCKER_USER}/${name}:latest"
        echo -e "${YELLOW}Also pushing ${latest_name}...${NC}"
        docker push "$latest_name"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully pushed ${image_name}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to push ${image_name}${NC}"
        return 1
    fi
}

# Check if logged into Docker Hub
if [ "$PUSH" = true ]; then
    echo "Checking Docker Hub authentication..."
    if ! docker info | grep -q "Username"; then
        echo -e "${RED}Not logged into Docker Hub. Run: docker login${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Hub authentication confirmed${NC}"
    echo ""
fi

# Build girder (main app with OAuth plugin)
echo ""
echo -e "${GREEN}[1/3] Building girder image (contains OAuth changes)${NC}"
echo "========================================================"
# Use repo root as context so we can access plugins/oauth
build_image "nci-dsa-deid" "$REPO_ROOT" "$REPO_ROOT/devops/nci-dsa-deid/Dockerfile"

# Build nginx (reverse proxy with routing config)
echo ""
echo -e "${GREEN}[2/3] Building nginx image${NC}"
echo "========================================================"
build_image "nci-dsa-deid-nginx" "$REPO_ROOT/services/nginx"

# Build reactdeid (React frontend)
echo ""
echo -e "${GREEN}[3/3] Building reactdeid image${NC}"
echo "========================================================"
build_image "reactdeid" "$REPO_ROOT/services/reactdeid"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Summary${NC}"
echo -e "${GREEN}========================================${NC}"
docker images | grep -E "REPOSITORY|${DOCKER_USER}/(nci-dsa-deid|reactdeid)" | head -20

# Push if requested
if [ "$PUSH" = true ]; then
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Pushing images to Docker Hub${NC}"
    echo -e "${YELLOW}========================================${NC}"
    
    push_image "nci-dsa-deid"
    push_image "nci-dsa-deid-nginx"
    push_image "reactdeid"
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All images pushed successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Colleagues can now pull these images:${NC}"
    echo ""
    echo "  cd devops/nci-dsa-deid"
    echo "  # Remove or rename docker-compose.override.yml"
    echo "  docker-compose pull"
    echo "  docker-compose up -d"
    echo ""
    echo -e "${BLUE}Available images:${NC}"
    echo "  ${DOCKER_USER}/nci-dsa-deid:${TAG}"
    echo "  ${DOCKER_USER}/nci-dsa-deid-nginx:${TAG}"
    echo "  ${DOCKER_USER}/reactdeid:${TAG}"
else
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Images built but NOT pushed${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo ""
    echo -e "${BLUE}To test locally:${NC}"
    echo "  cd devops/nci-dsa-deid"
    echo "  docker-compose up -d"
    echo ""
    echo -e "${BLUE}To push to Docker Hub:${NC}"
    echo "  $0 --push"
    echo ""
    echo -e "${BLUE}Or push with a version tag:${NC}"
    echo "  $0 --push --tag v1.2.3"
    echo ""
    echo -e "${BLUE}Or push manually:${NC}"
    echo "  docker push ${DOCKER_USER}/nci-dsa-deid:${TAG}"
    echo "  docker push ${DOCKER_USER}/nci-dsa-deid-nginx:${TAG}"
    echo "  docker push ${DOCKER_USER}/reactdeid:${TAG}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Workflow Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}For YOU (local development):${NC}"
echo "  1. Keep docker-compose.override.yml in place"
echo "  2. Make code changes"
echo "  3. Run: ./build-and-push.sh (test locally)"
echo "  4. Run: ./build-and-push.sh --push (push to registry)"
echo ""
echo -e "${BLUE}For COLLEAGUES (pull pre-built):${NC}"
echo "  1. Remove/rename docker-compose.override.yml"
echo "  2. Run: docker-compose pull"
echo "  3. Run: docker-compose up -d"
echo ""
echo -e "${GREEN}Done!${NC}"
