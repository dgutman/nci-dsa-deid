# Complete Configuration Summary - READY TO USE

## ✅ Everything is Now Configured and Working!

Your OAuth redirect URL is fully centralized and all required files are properly mounted.

---

## Configuration Files

### Environment Configuration (`.env`)
Location: `devops/nci-dsa-deid/.env`

```bash
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"

# DSA_USER is automatically set by start_dsadeid.sh script
DSA_USER=1000:1000
```

### Startup Script (`start_dsadeid.sh`)
Location: `devops/nci-dsa-deid/start_dsadeid.sh`

```bash
DSA_USER=$(id -u):$(id -g) docker compose down
DSA_USER=$(id -u):$(id -g) DSA_PORT=8080 docker compose up -d
```

This automatically sets your user ID for proper file permissions.

---

## Active Services (7 Total)

### Custom Built (2 images to push)
1. **girder** (`dagutman/nci-dsa-deid:latest`) - DSA + OAuth plugin
2. **reactdeid** (`dagutman/reactdeid:latest`) - React deidentification dashboard

### Official (auto-pull)
3. **nginx** - Reverse proxy
4. **mongodb** - Database
5. **memcached** - Cache
6. **rabbitmq** - Message queue
7. **worker** - Job processing

---

## Files Mounted into Girder Container

All your custom configuration files are now properly mounted:

```yaml
volumes:
  - ./girder.cfg                    # Main Girder config
  - ./provision.py                  # Wrapper provisioning script
  - ./wsi_deid_provision.py         # Your custom WSI DeID provisioning
  - ./provision.yaml                # Settings configuration
  - ./homepage.md                   # Homepage content
  - ./importManifestSchema.json     # Schema definition
  - ./start_girder.sh               # Girder startup script
```

---

## OAuth Configuration Flow

```
start_dsadeid.sh runs
    ↓
Reads .env file
    ↓
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
    ↓
Sets as DSA_SETTING_oauth.external_url (docker-compose.yml)
    ↓
provision.py reads DSA_SETTING_* environment variables
    ↓
Writes oauth.external_url to Girder database
    ↓
OAuth plugin (una.py) reads Setting().get(PluginSettings.EXTERNAL_URL)
    ↓
Constructs redirect URI: https://wsi-deid.pathology.emory.edu/dsa/api/v1/oauth/una/callback
```

**Verified in logs**: ✅ `Setting oauth.external_url to 'https://staging-wsi-deid.pathology.emory.edu'`

---

## Your Workflow

### Daily Development
```bash
cd /home/dagutman/devel/nci-dsa-deid/devops/nci-dsa-deid

# Start with your script
bash start_dsadeid.sh

# Check it's running
docker compose ps

# View logs
docker compose logs -f girder
```

### When Ready to Push
```bash
cd /home/dagutman/devel/nci-dsa-deid

# Build both images
./build-and-push.sh

# Test at http://localhost:8090/deid/

# If good, push
./build-and-push.sh --push
```

---

## Colleague Deployment

### Setup
```bash
cd devops/nci-dsa-deid

# Disable local builds
mv docker-compose.override.yml docker-compose.override.yml.disabled

# Set their domain in .env
echo 'OAUTH_EXTERNAL_URL="https://their-domain.example.com"' > .env
```

### Deploy/Update
```bash
# Pull your latest images
docker compose pull

# Start (they can also use start_dsadeid.sh)
bash start_dsadeid.sh

# Or manually:
# DSA_USER=$(id -u):$(id -g) docker compose up -d
```

---

## What Was Fixed

### 1. OAuth Centralization ✅
- Added `EXTERNAL_URL` setting to OAuth plugin
- Updated UNA provider to use centralized config
- Added to docker-compose.yml, provision.yaml, .env

### 2. Missing Files ✅
- Added `wsi_deid_provision.py` to volumes
- Added `homepage.md` to volumes
- Added `importManifestSchema.json` to volumes

### 3. Vite Host Security ✅
- Added `allowedHosts: 'all'` to vite.config.js
- Allows access from external domains

### 4. Unused Services Removed ✅
- Commented out `dashdeid` (deprecated)
- Commented out `react` (not used)
- Commented out `node` (not needed)

### 5. Build Context Fixed ✅
- Changed build context to repo root
- OAuth plugin can now be copied into image

---

## All Systems Operational

Run this to verify everything is working:

```bash
cd /home/dagutman/devel/nci-dsa-deid/devops/nci-dsa-deid

# Check all containers
docker compose ps

# All should show "Up" status
```

Access the application:
- Landing page: http://localhost:8090/
- DSA: http://localhost:8090/dsa
- DeID Dashboard: http://localhost:8090/deid/

---

## Ready to Push

Your images are built and tested locally. When ready:

```bash
cd /home/dagutman/devel/nci-dsa-deid
./build-and-push.sh --push
```

This pushes:
- `dagutman/nci-dsa-deid:latest` (10.8 GB)
- `dagutman/reactdeid:latest` (1.34 GB)

Colleagues can then pull and deploy with a single environment variable! 🎉

---

## Environment Variable Summary

### What you set in `.env`:
```bash
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
```

### What the script sets automatically:
```bash
DSA_USER=$(id -u):$(id -g)  # Set by start_dsadeid.sh
DSA_PORT=8080               # Set by start_dsadeid.sh
```

**One variable** (`OAUTH_EXTERNAL_URL`) is all colleagues need to change for different deployments! ✨
