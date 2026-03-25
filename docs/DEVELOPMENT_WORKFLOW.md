# Development and Deployment Workflow

This document explains how to develop locally, build images, and deploy so colleagues can pull pre-built images.

## Quick Reference

### For Developers (YOU)
```bash
# Local development with live builds
cd devops/nci-dsa-deid
docker-compose up -d              # Uses override file, builds locally

# Build and test
./build-and-push.sh               # Build all images locally

# Push to registry for colleagues
./build-and-push.sh --push        # Build and push to Docker Hub
```

### For Colleagues/IT (THEM)
```bash
# Pull pre-built images (no building)
cd devops/nci-dsa-deid
mv docker-compose.override.yml docker-compose.override.yml.disabled  # Disable local builds
docker-compose pull               # Download from Docker Hub
docker-compose up -d              # Start services
```

---

## Understanding the Setup

### Two Compose Files

**1. `docker-compose.yml`** (Main configuration)
- Defines all services
- Uses pre-built images from Docker Hub
- Default behavior: **PULL** images from registry
- Used by colleagues and production deployments

**2. `docker-compose.override.yml`** (Development overrides)
- Automatically loaded if present
- Adds `build:` sections for local development
- Overrides image pull behavior with local builds
- Used only for local development

### How Docker Compose Works

```bash
# With docker-compose.override.yml present:
docker-compose up -d
# → Builds images locally from Dockerfiles

# Without docker-compose.override.yml:
docker-compose up -d
# → Pulls pre-built images from Docker Hub
```

---

## Developer Workflow (Local Development & Push)

### Initial Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/dgutman/nci-dsa-deid.git
   cd nci-dsa-deid
   ```

2. **Ensure override file exists**
   ```bash
   ls devops/nci-dsa-deid/docker-compose.override.yml
   # Should exist - this enables local building
   ```

3. **Login to Docker Hub** (only once)
   ```bash
   docker login
   # Enter username: dagutman
   # Enter password: [your Docker Hub token]
   ```

### Daily Development

1. **Make code changes** to:
   - OAuth plugin (`plugins/oauth/`)
   - React app (`services/reactdeid/`)
   - Girder configuration (`devops/nci-dsa-deid/`)

2. **Test locally**
   ```bash
   cd devops/nci-dsa-deid
   
   # Use the startup script (sets DSA_USER automatically)
   bash start_dsadeid.sh
   
   # Or manually:
   # docker-compose build
   # DSA_USER=$(id -u):$(id -g) docker compose up -d
   
   # Check logs
   docker compose logs -f girder
   
   # Test the application
   # Open browser to http://localhost:8090
   ```

3. **When ready to share with colleagues**
   ```bash
   cd /home/dagutman/devel/nci-dsa-deid
   
   # Build all images
   ./build-and-push.sh
   
   # If tests pass, push to Docker Hub
   ./build-and-push.sh --push
   ```

4. **Notify colleagues**
   ```bash
   # Send message: "New images pushed! Pull and test with:
   #   docker compose pull && docker compose up -d"
   ```

### Build Script Options

```bash
# Build only (test locally first)
./build-and-push.sh

# Build and push with latest tag
./build-and-push.sh --push

# Build and push with version tag
./build-and-push.sh --push --tag v1.2.3

# Set custom Docker Hub username
DOCKER_USER=myusername ./build-and-push.sh --push
```

---

## Colleague/IT Workflow (Pull Pre-built Images)

### Initial Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/dgutman/nci-dsa-deid.git
   cd nci-dsa-deid/devops/nci-dsa-deid
   ```

2. **Disable local building**
   ```bash
   # Rename the override file to prevent local builds
   mv docker-compose.override.yml docker-compose.override.yml.disabled
   
   # OR delete it
   # rm docker-compose.override.yml
   ```

3. **Set environment variable**
   ```bash
   # Create .env file
   cp ../../example.env .env
   
   # Edit .env and set your domain
   echo 'OAUTH_EXTERNAL_URL="https://your-domain.example.com"' >> .env
   ```

### Pull and Deploy

```bash
cd devops/nci-dsa-deid

# Pull latest images from Docker Hub
docker-compose pull

# Start services
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f girder
```

### Update to Latest Version

```bash
cd devops/nci-dsa-deid

# Pull latest images
docker-compose pull

# Restart with new images
docker-compose down
docker-compose up -d
```

---

## Images Built and Pushed

| Image | Purpose | Build Time | Needs Push? |
|-------|---------|------------|-------------|
| `dagutman/nci-dsa-deid:latest` | Girder + OAuth plugin | ~5-10 min | ✅ YES |
| `dagutman/reactdeid:latest` | React deidentification app | ~2-3 min | ✅ YES |
| `dagutman/dashncidsadeidapp:latest` | Legacy Dash app | ~2-3 min | ✅ YES |
| `nginx:1.27.1` | Web server | - | ❌ NO (official) |
| `mongo:latest` | Database | - | ❌ NO (official) |
| `memcached` | Cache | - | ❌ NO (official) |
| `rabbitmq:latest` | Message queue | - | ❌ NO (official) |
| `dsarchive/dsa_common` | DSA worker | - | ❌ NO (upstream) |

---

## Troubleshooting

### "Image not found" when colleague runs docker-compose pull

**Cause**: Image wasn't pushed to Docker Hub

**Solution**:
```bash
# Developer: Push the image
./build-and-push.sh --push

# Colleague: Try again
docker-compose pull
```

### Colleague's deployment uses old code

**Cause**: Docker compose is building locally instead of pulling

**Solution**:
```bash
# Check if override file exists
ls docker-compose.override.yml

# If exists, disable it
mv docker-compose.override.yml docker-compose.override.yml.disabled

# Force pull and recreate
docker-compose pull
docker-compose up -d --force-recreate
```

### Local development keeps pulling instead of building

**Cause**: Missing or renamed `docker-compose.override.yml`

**Solution**:
```bash
# Check if override file exists
ls docker-compose.override.yml

# If missing, restore it
git checkout docker-compose.override.yml

# Or rename back
mv docker-compose.override.yml.disabled docker-compose.override.yml
```

### Build fails with "permission denied"

**Cause**: Not logged into Docker Hub

**Solution**:
```bash
docker login
# Enter credentials

# Try again
./build-and-push.sh --push
```

### Different behavior between local and colleague's deployment

**Checklist**:
- [ ] Did you push the latest build? `./build-and-push.sh --push`
- [ ] Did colleague pull latest? `docker-compose pull`
- [ ] Did colleague restart? `docker-compose up -d --force-recreate`
- [ ] Is colleague's override file disabled? `ls docker-compose.override.yml` should not exist
- [ ] Are environment variables set correctly? Check `.env` file

---

## File Reference

### Key Files

- **`build-and-push.sh`** - Script to build and push images
- **`docker-compose.yml`** - Main service definitions (pulls images)
- **`docker-compose.override.yml`** - Local dev overrides (builds images)
- **`.env`** - Environment variables (OAUTH_EXTERNAL_URL)
- **`example.env`** - Template for environment variables

### For Local Development

Keep these files:
- ✅ `docker-compose.yml`
- ✅ `docker-compose.override.yml` (enables building)
- ✅ `.env` (with localhost URL)

### For Colleague/Production Deployment

Keep these files:
- ✅ `docker-compose.yml`
- ❌ `docker-compose.override.yml` (remove/rename)
- ✅ `.env` (with production URL)

---

## Environment Variables

### OAUTH_EXTERNAL_URL

**Purpose**: Sets the public-facing domain for OAuth redirect URIs

**For developer (local)**:
```bash
OAUTH_EXTERNAL_URL="http://localhost:8090"
```

**For colleague (staging)**:
```bash
OAUTH_EXTERNAL_URL="https://staging-wsi-deid.pathology.emory.edu"
```

**For production**:
```bash
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
```

This is the **whole point** of the centralization - same images work everywhere with different URLs!

---

## Summary

### Developer (You)
1. Keep `docker-compose.override.yml` ✅
2. Make code changes
3. Test locally: `docker-compose up -d` (builds automatically)
4. Push when ready: `./build-and-push.sh --push`

### Colleague/IT (Them)
1. Remove `docker-compose.override.yml` ❌
2. Set `OAUTH_EXTERNAL_URL` in `.env`
3. Pull images: `docker-compose pull`
4. Deploy: `docker-compose up -d`

**Result**: Same images, different environments, no rebuilding required! 🎉
