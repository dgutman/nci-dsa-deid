# OAuth Configuration Migration Guide for IT

## Quick Summary

We've centralized OAuth redirect URL configuration to fix deployment issues. Instead of hardcoded values, the system now uses a single environment variable: **`OAUTH_EXTERNAL_URL`**

## What Changed

### Before
- OAuth redirect URLs were hardcoded in the codebase
- Each deployment to a new domain required code changes
- Multiple files had the same domain repeated

### After
- Single environment variable: `OAUTH_EXTERNAL_URL`
- Set once per environment
- Automatically propagates to all components

## Migration Steps

### Step 1: Set Environment Variable

Add this to your environment configuration (`.env` file or system environment):

```bash
OAUTH_EXTERNAL_URL="https://your-production-domain.example.com"
```

**Important Notes:**
- Use the full URL with protocol (https://)
- Do NOT include trailing slash
- Do NOT include path segments (like `/dsa` or `/api`)
- This should be the public-facing domain users access

**Examples:**
```bash
# Production
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"

# Staging
OAUTH_EXTERNAL_URL="https://staging-wsi-deid.pathology.emory.edu"

# Test
OAUTH_EXTERNAL_URL="https://test-wsi-deid.pathology.emory.edu"
```

### Step 2: Update Docker Compose (if using custom config)

If you have a custom `docker-compose.yml` or `docker-compose.override.yml`, ensure the girder service has:

```yaml
services:
  girder:
    environment:
      DSA_SETTING_oauth.external_url: ${OAUTH_EXTERNAL_URL:-https://wsi-deid.pathology.emory.edu}
```

The default configuration in the repo already includes this.

### Step 3: Restart Services

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Step 4: Verify Configuration

1. Check the environment variable is set:
   ```bash
   docker-compose exec girder printenv | grep OAUTH
   ```
   
   Expected output:
   ```
   OAUTH_EXTERNAL_URL=https://your-domain.example.com
   DSA_SETTING_oauth.external_url=https://your-domain.example.com
   ```

2. Check Girder logs for OAuth configuration:
   ```bash
   docker-compose logs girder | grep "oauth.external_url"
   ```
   
   Expected output:
   ```
   Setting oauth.external_url to 'https://your-domain.example.com'
   ```

3. Test OAuth login:
   - Navigate to your deployment
   - Click "Login with UNA"
   - Check browser developer console for OAuth redirect URL
   - Should see: `redirect_uri=https://your-domain.example.com/dsa/api/v1/oauth/una/callback`

## Troubleshooting

### OAuth login fails with "redirect_uri mismatch"

**Cause**: The `OAUTH_EXTERNAL_URL` doesn't match the registered OAuth callback URL in the OAuth provider (UNA).

**Solution**:
1. Verify `OAUTH_EXTERNAL_URL` matches your deployment domain
2. Ensure the OAuth application (UNA) has the correct callback URL registered:
   - Format: `https://your-domain.example.com/dsa/api/v1/oauth/una/callback`
   - Contact OAuth administrator to update if needed

### Environment variable not taking effect

**Cause**: Environment variable not properly passed to container or cache issue.

**Solution**:
```bash
# Check if variable is in the container
docker-compose exec girder printenv | grep OAUTH

# If not present, check your .env file
cat .env | grep OAUTH

# Rebuild and restart with --force-recreate
docker-compose down
docker-compose up -d --force-recreate girder

# Check Girder startup logs
docker-compose logs -f girder
```

### Setting shows old value in Girder admin

**Cause**: Setting was previously set in database and isn't being overridden.

**Solution**:
```bash
# Option 1: Force update via provision (recommended)
docker-compose exec girder python -c "
from girder.models.setting import Setting
from girder_oauth.settings import PluginSettings
Setting().set('oauth.external_url', 'https://your-domain.example.com')
print('Updated oauth.external_url')
"

# Option 2: Clear the setting and restart (will use environment variable)
docker-compose exec girder python -c "
from girder.models.setting import Setting
Setting().unset('oauth.external_url')
print('Cleared oauth.external_url - will be set from env on restart')
"
docker-compose restart girder
```

## Production Deployment Checklist

- [ ] Set `OAUTH_EXTERNAL_URL` environment variable
- [ ] Update `.env` file in deployment directory
- [ ] Pull latest code from repository
- [ ] Rebuild Docker images: `docker-compose build`
- [ ] Restart services: `docker-compose up -d`
- [ ] Verify environment variable in container
- [ ] Check Girder logs for setting confirmation
- [ ] Test OAuth login
- [ ] Verify OAuth callback URL in browser console
- [ ] Monitor application logs for any OAuth errors

## Multiple Environments

If you manage multiple environments (dev, staging, production), each should have its own `OAUTH_EXTERNAL_URL`:

### Development
```bash
OAUTH_EXTERNAL_URL="http://localhost:8090"
# or
OAUTH_EXTERNAL_URL="https://dev-wsi-deid.pathology.emory.edu"
```

### Staging
```bash
OAUTH_EXTERNAL_URL="https://staging-wsi-deid.pathology.emory.edu"
```

### Production
```bash
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
```

## Security Considerations

- **HTTPS Required**: Production deployments MUST use HTTPS
- **Environment Variables**: Store `.env` file securely (not in version control)
- **OAuth Callback URLs**: Ensure OAuth provider (UNA) has only approved domains registered

## Support

If you encounter issues during migration:

1. Check logs: `docker-compose logs girder | tail -100`
2. Verify environment: `docker-compose config | grep OAUTH`
3. Review [OAUTH_CONFIGURATION.md](./OAUTH_CONFIGURATION.md) for detailed technical information
4. Contact development team with logs and error messages

## Rollback

If you need to rollback:

1. The code maintains backward compatibility with hardcoded values
2. Simply remove `OAUTH_EXTERNAL_URL` from environment
3. System will fall back to hardcoded `https://wsi-deid.pathology.emory.edu`
4. Note: This defeats the purpose of the migration and should only be used as emergency measure
