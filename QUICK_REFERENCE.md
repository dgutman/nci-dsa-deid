# Quick Reference: Build, Test, Push Workflow

## Your Workflow (Developer)

### 1. Local Development & Testing
```bash
cd /home/dagutman/devel/nci-dsa-deid/devops/nci-dsa-deid

# Use the startup script (automatically sets DSA_USER)
bash start_dsadeid.sh

# Check logs
docker compose logs -f girder

# Test at http://localhost:8090
```

### 2. Build All Images
```bash
cd /home/dagutman/devel/nci-dsa-deid

# Build images (don't push yet)
./build-and-push.sh
```

### 3. Push to Registry (After Testing)
```bash
# Push to Docker Hub for colleagues
./build-and-push.sh --push

# Or with a version tag
./build-and-push.sh --push --tag v1.2.3
```

---

## Colleague's Workflow (Tester/IT)

### First Time Setup
```bash
cd /home/dagutman/devel/nci-dsa-deid/devops/nci-dsa-deid

# Disable local builds
mv docker-compose.override.yml docker-compose.override.yml.disabled

# Set domain
echo 'OAUTH_EXTERNAL_URL="https://their-domain.com"' > .env
```

### Pull and Test
```bash
# Pull latest images from Docker Hub
docker-compose pull

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f girder

# Test at their domain
```

---

## What Happens?

### With `docker-compose.override.yml` (Developer)
```
docker-compose up -d
    ↓
Reads docker-compose.yml + docker-compose.override.yml
    ↓
Sees build: sections from override file
    ↓
BUILDS images locally from Dockerfiles
    ↓
Uses locally built images
```

### Without `docker-compose.override.yml` (Colleague)
```
docker-compose pull
    ↓
Reads docker-compose.yml only
    ↓
Sees image: dagutman/nci-dsa-deid:latest
    ↓
PULLS pre-built image from Docker Hub
    ↓
Uses registry image (no building!)
```

---

## Key Points

✅ **Same docker-compose.yml for everyone**
- Developer sees: pull images OR build (if override present)
- Colleague sees: pull images only

✅ **Environment variable flows at runtime**
- No rebuild needed for different domains
- Just change OAUTH_EXTERNAL_URL

✅ **One command to share your work**
- `./build-and-push.sh --push`
- Done!

---

## Files to Keep/Remove

### Developer (You)
- ✅ Keep `docker-compose.override.yml`
- ✅ Keep `.env` with localhost URL

### Colleague (Them)
- ❌ Remove `docker-compose.override.yml`
- ✅ Keep `.env` with their domain URL

---

## Troubleshooting

### Colleague says "Image not found"
```bash
# You forgot to push!
./build-and-push.sh --push
```

### Colleague's app has old code
```bash
# They need to pull fresh
docker-compose pull
docker-compose up -d --force-recreate
```

### Your local build keeps pulling instead
```bash
# You removed the override file by accident
git checkout docker-compose.override.yml
```

---

## Images Pushed

After `./build-and-push.sh --push`:

1. `dagutman/nci-dsa-deid:latest` (Girder + OAuth)
2. `dagutman/reactdeid:latest` (React app)  
3. `dagutman/dashncidsadeidapp:latest` (Dash app)

All available on Docker Hub for colleagues to pull!
