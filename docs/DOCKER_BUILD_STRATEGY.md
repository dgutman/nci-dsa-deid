# Docker Container Build & Registry Strategy

## Current Container Status

### Services Overview

| Service | Image Source | Build Config | Push to Registry? | Notes |
|---------|--------------|--------------|-------------------|-------|
| **girder** | `dagutman/nci-dsa-deid:latest` | Dockerfile exists (commented in compose) | ✅ YES | **MAIN APP** - Contains OAuth changes |
| **nginx** | `nginx:1.27.1` | Official image | ❌ NO | Uses official nginx, config via volumes |
| **mongodb** | `mongo:latest` | Official image | ❌ NO | Official mongo image |
| **memcached** | `memcached` | Official image | ❌ NO | Official memcached image |
| **rabbitmq** | `rabbitmq:latest` | Official image | ❌ NO | Official rabbitmq image |
| **worker** | `dsarchive/dsa_common` | Official DSA image | ❌ NO | Upstream DSA worker |
| **dashdeid** | `dagutman/dashncidsadeidapp` | ✅ Local build | ✅ YES | Legacy Dash app |
| **reactdeid** | `reactdeid:latest` | ✅ Local build | ✅ YES | **NEW React app** |
| **react** | `bdsa/bdsa-react:0.0.4` | ✅ Local build | ⚠️ OPTIONAL | Old react app? |
| **node** | `bdsa/bdsa-node:0.0.1` | ✅ Local build | ⚠️ OPTIONAL | Express API server |

## Critical Images That MUST Be Rebuilt & Pushed

### 1. **girder** (dagutman/nci-dsa-deid:latest) 🔴 CRITICAL

**Why rebuild?**: Contains the OAuth plugin with your centralized configuration changes

**Location**: `devops/nci-dsa-deid/Dockerfile`

**Build command**:
```bash
cd devops/nci-dsa-deid
docker build -t dagutman/nci-dsa-deid:latest .
```

**Push command**:
```bash
docker push dagutman/nci-dsa-deid:latest
```

**Note**: The build section is currently commented out in docker-compose.yml (lines 4-5). You need to:
- Build and push this image
- OR uncomment the build section for local development

### 2. **reactdeid** (reactdeid:latest) 🟡 IMPORTANT

**Why?**: The new React deidentification app

**Location**: `services/reactdeid/Dockerfile`

**Build command**:
```bash
cd services/reactdeid
docker build -t dagutman/reactdeid:latest .
# Or with your Docker Hub username
docker build -t yourusername/reactdeid:latest .
```

**Push command**:
```bash
docker push dagutman/reactdeid:latest
```

**Update docker-compose.yml**:
```yaml
reactdeid:
  image: dagutman/reactdeid:latest  # Change from just 'reactdeid:latest'
  build:
    context: ../../services/reactdeid
```

### 3. **dashdeid** (dagutman/dashncidsadeidapp) 🟢 OPTIONAL

**Why?**: Legacy Dash app (might be deprecated?)

**Location**: `services/dashdeid/Dockerfile`

**Build & push**:
```bash
cd services/dashdeid
docker build -t dagutman/dashncidsadeidapp:latest .
docker push dagutman/dashncidsadeidapp:latest
```

## Images That DON'T Need Registry Push

### 4. **react** (bdsa/bdsa-react:0.0.4) - Local development only?
### 5. **node** (bdsa/bdsa-node:0.0.1) - Local development only?

These seem to be for local development with volume mounts. If IT doesn't need these services, they might be optional.

## Recommended Strategy

### For Production IT Deployment

**Option A: Pull Pre-built Images (Recommended)**

1. Build and push the 2 critical images:
   - `dagutman/nci-dsa-deid:latest` (girder with OAuth changes)
   - `dagutman/reactdeid:latest` (React app)

2. Update docker-compose.yml to use full image names:
   ```yaml
   reactdeid:
     image: dagutman/reactdeid:latest
     # Comment out build section for production
     # build:
     #   context: ../../services/reactdeid
   ```

3. IT can simply run:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

**Option B: Build Locally (Development)**

Keep build sections uncommented, IT builds on their servers:
```bash
docker-compose build
docker-compose up -d
```

### For Your Development Setup

**Recommended docker-compose configuration**:

```yaml
services:
  girder:
    image: "dagutman/nci-dsa-deid:latest"
    build:  # Uncomment for local development
      context: .
      dockerfile: Dockerfile
    # ... rest of config

  reactdeid:
    image: dagutman/reactdeid:latest
    build:  # Keep for local development
      context: ../../services/reactdeid
      args:
        - NODE_ENV=development
    # ... rest of config
```

This way:
- Local dev can build with `docker-compose build`
- Production can pull with `docker-compose pull`

## Step-by-Step: Rebuild & Push Critical Images

### 1. Rebuild Girder (with OAuth changes)

```bash
cd /home/dagutman/devel/nci-dsa-deid/devops/nci-dsa-deid

# Build the image
docker build -t dagutman/nci-dsa-deid:latest .

# Test locally first
docker-compose up -d girder

# If working, push to registry
docker push dagutman/nci-dsa-deid:latest
```

### 2. Rebuild ReactDeid

```bash
cd /home/dagutman/devel/nci-dsa-deid/services/reactdeid

# Build the image
docker build -t dagutman/reactdeid:latest .

# Test locally
cd /home/dagutman/devel/nci-dsa-deid/devops/nci-dsa-deid
docker-compose up -d reactdeid

# If working, push to registry
docker push dagutman/reactdeid:latest
```

### 3. Update docker-compose.yml for Production

```yaml
services:
  girder:
    image: "dagutman/nci-dsa-deid:latest"
    # build:  # Comment out for production pull
    #   context: .
    
  reactdeid:
    image: dagutman/reactdeid:latest  # Update from just 'reactdeid:latest'
    # build:  # Comment out for production pull
    #   context: ../../services/reactdeid
```

## What IT Needs

After you push the images, IT just needs:

1. **Pull images**:
   ```bash
   docker-compose pull
   ```

2. **Set environment variable**:
   ```bash
   export OAUTH_EXTERNAL_URL="https://their-domain.com"
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

**No building required on their end!**

## Docker Hub Authentication

If pushing to Docker Hub:

```bash
# Login to Docker Hub
docker login

# Enter your username and password

# Now you can push
docker push dagutman/nci-dsa-deid:latest
docker push dagutman/reactdeid:latest
```

## Verification

After pushing, verify others can pull:

```bash
# On a different machine or after removing local images
docker pull dagutman/nci-dsa-deid:latest
docker pull dagutman/reactdeid:latest

# Should download from Docker Hub
```

## Summary

### Must Rebuild & Push (for OAuth changes)
1. ✅ **girder** - `dagutman/nci-dsa-deid:latest`
2. ✅ **reactdeid** - `dagutman/reactdeid:latest` (update name in compose)

### Optional (if used)
3. ⚠️ **dashdeid** - `dagutman/dashncidsadeidapp:latest`
4. ⚠️ **react** - Local dev only?
5. ⚠️ **node** - Local dev only?

### Don't Touch (official images)
- nginx, mongodb, memcached, rabbitmq, worker - all pull from official registries

## Next Steps

1. Uncomment girder build section in docker-compose.yml temporarily
2. Build girder image: `docker build -t dagutman/nci-dsa-deid:latest .`
3. Build reactdeid image: `docker build -t dagutman/reactdeid:latest services/reactdeid/`
4. Test locally with new images
5. Push to Docker Hub: `docker push dagutman/nci-dsa-deid:latest && docker push dagutman/reactdeid:latest`
6. Comment build sections back out for production
7. Notify IT that new images are available

Would you like me to help you create a build script to automate this?
