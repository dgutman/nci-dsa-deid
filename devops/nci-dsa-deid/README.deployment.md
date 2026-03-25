# NCI-DSA-DEID Deployment

This directory contains the Docker Compose configuration for the NCI-DSA-DEID application.

## Quick Start

### For Development (Building Locally)
```bash
# Keep docker-compose.override.yml in place
docker-compose build
docker-compose up -d
```

### For Production/Colleagues (Pull Pre-built)
```bash
# Remove docker-compose.override.yml
mv docker-compose.override.yml docker-compose.override.yml.disabled

# Set your domain
echo 'OAUTH_EXTERNAL_URL="https://your-domain.example.com"' > .env

# Pull and start
docker-compose pull
docker-compose up -d
```

## Files

- **docker-compose.yml** - Main service definitions (uses pre-built images)
- **docker-compose.override.yml** - Local development overrides (enables building)
- **Dockerfile** - Builds the main girder service with OAuth plugin
- **.env** - Environment variables (create from ../../example.env)

## Images

Pre-built images are available on Docker Hub:
- `dagutman/nci-dsa-deid:latest` - Main girder service
- `dagutman/reactdeid:latest` - React frontend
- `dagutman/dashncidsadeidapp:latest` - Dash app

## Configuration

### Required Environment Variable

Set `OAUTH_EXTERNAL_URL` to your deployment's public domain:

```bash
# .env file
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
```

This centralizes OAuth redirect URL configuration across all services.

## Documentation

- [Development Workflow](../../docs/DEVELOPMENT_WORKFLOW.md) - How to develop locally and push images
- [OAuth Configuration](../../docs/OAUTH_CONFIGURATION.md) - Technical details of OAuth setup
- [OAuth Migration Guide](../../docs/OAUTH_MIGRATION_GUIDE.md) - IT deployment guide
- [Docker Build Strategy](../../docs/DOCKER_BUILD_STRATEGY.md) - Image build and registry strategy

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Review documentation above
3. Contact development team
