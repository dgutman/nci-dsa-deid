# Final Stack Configuration

## ✅ Active Services (7 total)

### Custom Built Services (Need to Build & Push)

1. **girder** (`dagutman/nci-dsa-deid:latest`)
   - Main DSA backend with OAuth plugin
   - Contains your OAuth centralization changes
   - Route: `/dsa`

2. **reactdeid** (`dagutman/reactdeid:latest`)
   - React deidentification dashboard
   - Primary user interface
   - Route: `/deid/`

### Official Images (Auto-Pull)

3. **nginx** (`nginx:1.27.1`)
   - Reverse proxy and static file server
   - Serves landing page at `/`
   - No build needed

4. **mongodb** (`mongo:latest`)
   - Database for Girder
   - No build needed

5. **memcached** (`memcached`)
   - Cache for large_image tiles
   - No build needed

6. **rabbitmq** (`rabbitmq:latest`)
   - Message queue for async jobs
   - No build needed

7. **worker** (`dsarchive/dsa_common`)
   - Celery worker for job processing
   - No build needed

---

## ❌ Removed/Deprecated Services

- **dashdeid** - Legacy Dash app (replaced by reactdeid)
- **react** - Old specimen management app (not routed in nginx)
- **node** - Express API stub (not used by reactdeid)

---

## Build & Push Commands

### Simple: Build and Push Both Images
```bash
cd /home/dagutman/devel/nci-dsa-deid

# Build locally first (test)
./build-and-push.sh

# If tests pass, push to Docker Hub
./build-and-push.sh --push
```

### With Version Tag
```bash
./build-and-push.sh --push --tag v1.0.0
```

This pushes:
- `dagutman/nci-dsa-deid:latest` (and v1.0.0 if tagged)
- `dagutman/reactdeid:latest` (and v1.0.0 if tagged)

---

## Colleague Deployment

### First Time Setup
```bash
cd devops/nci-dsa-deid

# Disable local builds
mv docker-compose.override.yml docker-compose.override.yml.disabled

# Set domain
echo 'OAUTH_EXTERNAL_URL="https://their-domain.com"' > .env
```

### Deploy/Update
```bash
# Pull latest images from Docker Hub
docker compose pull

# Start services
docker compose up -d

# Verify
docker compose ps
docker compose logs -f girder
```

---

## What Changed from Earlier

### Removed:
- `dashdeid` service (you confirmed it's deprecated)
- `react` service (old app, not used)
- `node` service (stub API, not called by reactdeid)
- Nginx routes for these services

### Result:
- ✅ Cleaner stack (7 services instead of 10)
- ✅ No more pull errors for `bdsa/bdsa-react`
- ✅ Only 2 images to build and push
- ✅ Faster builds and deployments

---

## Final Architecture

```
User
  ↓
nginx (port 8090)
  ├─ / → Static HTML (landing page)
  ├─ /dsa → girder:8080 (DSA backend)
  └─ /deid/ → reactdeid:5173 (Deidentification dashboard)

girder
  ├─ mongodb (database)
  ├─ memcached (cache)
  ├─ rabbitmq (message queue)
  └─ worker (job processing)
```

Simple and clean! 🎉

---

## Quick Commands

### You (Developer)
```bash
# Build locally
cd devops/nci-dsa-deid
docker compose build

# Test
docker compose up -d

# Push when ready
cd ../..
./build-and-push.sh --push
```

### Colleague (Production/Testing)
```bash
# Pull and deploy
cd devops/nci-dsa-deid
docker compose pull
docker compose up -d
```

---

## Images in Registry

After pushing, these will be available on Docker Hub:
- https://hub.docker.com/r/dagutman/nci-dsa-deid
- https://hub.docker.com/r/dagutman/reactdeid

Your colleagues can pull them without any Docker Hub account (public images).
