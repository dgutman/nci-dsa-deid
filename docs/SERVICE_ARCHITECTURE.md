# Service Architecture Overview

## Services and Their Roles

### Custom Built Images (Need to Push)

#### 1. **girder** (`dagutman/nci-dsa-deid:latest`)
- **Purpose**: Main DSA (Digital Slide Archive) backend with OAuth plugin
- **Contains**: 
  - Girder server
  - OAuth plugin with centralized redirect URL config
  - WSI deid plugin
  - LDAP authentication
- **Access**: `/dsa`
- **Status**: ✅ **ACTIVE** - Contains your OAuth changes

#### 2. **reactdeid** (`dagutman/reactdeid:latest`)
- **Purpose**: React-based deidentification dashboard
- **Contains**:
  - Modern React/Vite frontend
  - Deidentification workflow UI
  - WSI processing interface
- **Access**: `/deid/`
- **Status**: ✅ **ACTIVE** - Main deidentification interface

#### 3. **node** (`dagutman/bdsa-node:0.0.1`)
- **Purpose**: Express API server for custom endpoints
- **Contains**:
  - Express.js API server
  - Handles `/api` routes
  - Custom backend logic separate from Girder
- **Access**: `/api`
- **Status**: ✅ **ACTIVE** - Your landing page API server

### Official/Upstream Images (Just Pull)

#### 4. **nginx** (`nginx:1.27.1`)
- **Purpose**: Reverse proxy and static file server
- **Contains**:
  - Routes requests to appropriate services
  - Serves landing page (static HTML at `/`)
  - SSL termination (if configured)
- **Access**: Port 8090 (external)
- **Status**: ✅ **ACTIVE** - No building needed

#### 5. **mongodb** (`mongo:latest`)
- **Purpose**: Database for Girder
- **Contains**: MongoDB database
- **Access**: Internal only (port 27017)
- **Status**: ✅ **ACTIVE** - No building needed

#### 6. **memcached** (`memcached`)
- **Purpose**: Caching layer for large_image tiles
- **Contains**: Memcached cache server
- **Access**: Internal only (port 11211)
- **Status**: ✅ **ACTIVE** - No building needed

#### 7. **rabbitmq** (`rabbitmq:latest`)
- **Purpose**: Message queue for async jobs
- **Contains**: RabbitMQ message broker
- **Access**: Internal only (port 5672)
- **Status**: ✅ **ACTIVE** - No building needed

#### 8. **worker** (`dsarchive/dsa_common`)
- **Purpose**: Celery worker for processing jobs
- **Contains**: 
  - Girder worker
  - Slicer CLI web tasks
  - Image processing tasks
- **Access**: Internal only
- **Status**: ✅ **ACTIVE** - No building needed

### Deprecated/Unused Services

#### 9. **dashdeid** (`dagutman/dashncidsadeidapp`)
- **Purpose**: Legacy Dash-based deidentification app
- **Status**: ❌ **DEPRECATED** - Replaced by reactdeid
- **Action**: Removed from build script

#### 10. **react** (`bdsa/bdsa-react:0.0.4`)
- **Purpose**: Unknown - possibly old frontend?
- **Status**: ⚠️ **UNKNOWN** - Check if still used
- **Action**: Not included in build script (optional)

---

## Request Routing (nginx)

```
http://localhost:8090/
    ↓
┌─────────────────────────────────────┐
│           nginx (port 80)           │
└─────────────────────────────────────┘
           │
           ├─ / → Static HTML (landing page)
           │
           ├─ /dsa → girder:8080
           │   └─ Digital Slide Archive
           │
           ├─ /deid/ → reactdeid:5173
           │   └─ React deidentification dashboard
           │
           ├─ /api → node:8080
           │   └─ Express API server
           │
           └─ /dashdeid → dashdeid:8050
               └─ (DEPRECATED - Legacy Dash app)
```

---

## What Gets Built & Pushed

### Required for OAuth Changes

1. **girder** - Contains OAuth plugin changes ✅
2. **reactdeid** - Frontend application ✅
3. **node** - API server for landing page ✅

### Build Command

```bash
./build-and-push.sh --push
```

This builds and pushes:
- `dagutman/nci-dsa-deid:latest`
- `dagutman/reactdeid:latest`
- `dagutman/bdsa-node:0.0.1`

---

## Landing Page

**Location**: `services/nginx/index.html`
**Served by**: nginx (static file)
**Container**: None (just a file mounted into nginx)
**Access**: `http://localhost:8090/`

The landing page is a static HTML file with links to:
- `/dsa` - Digital Slide Archive
- `/deid/` - DeID Dashboard

---

## Service Dependencies

```
Landing Page (nginx static)
    ↓
User clicks "Digital Slide Archive"
    ↓
nginx → /dsa → girder:8080
            ↓
        mongodb (database)
        memcached (cache)
        rabbitmq (queue)
        worker (jobs)

User clicks "DeID Dashboard"
    ↓
nginx → /deid/ → reactdeid:5173
            ↓
        Calls API → girder:8080

Custom API calls
    ↓
nginx → /api → node:8080
```

---

## Summary

### Build & Push These 3 Images:
1. ✅ **girder** (dagutman/nci-dsa-deid:latest) - OAuth changes
2. ✅ **reactdeid** (dagutman/reactdeid:latest) - React dashboard
3. ✅ **node** (dagutman/bdsa-node:0.0.1) - API server

### Don't Build (Official Images):
- nginx, mongodb, memcached, rabbitmq, worker

### Deprecated:
- ❌ dashdeid (old Dash app)
- ⚠️ react (unknown usage)

### Landing Page:
- Static HTML file in nginx, no container needed
