# OAuth Redirect URL Centralization - Implementation Summary

## Overview

Successfully centralized OAuth redirect URL configuration to resolve deployment issues where hardcoded domains caused failures when IT deployed to different environments.

## Changes Made

### 1. Core Configuration Files

#### `plugins/oauth/girder_oauth/settings.py`
- **Added**: `EXTERNAL_URL = "oauth.external_url"` setting constant
- **Modified**: Added to validators and defaults lists
- **Purpose**: Defines the Girder setting for storing the external OAuth URL

#### `plugins/oauth/girder_oauth/providers/una.py`
- **Modified**: `_normalizeRedirectUri()` method
  - Now reads from `Setting().get(PluginSettings.EXTERNAL_URL)`
  - Falls back to `os.environ.get('OAUTH_EXTERNAL_URL')`
  - Maintains backward compatibility with hardcoded fallback
  
- **Modified**: `getUrl()` method
  - Uses centralized external URL setting
  - Constructs OAuth redirect URI dynamically
  - Adds warning in logs if using fallback

### 2. Docker Configuration

#### `devops/nci-dsa-deid/docker-compose.yml`
- **Added to girder service**:
  ```yaml
  DSA_SETTING_oauth.external_url: ${OAUTH_EXTERNAL_URL:-https://wsi-deid.pathology.emory.edu}
  ```
  - The `DSA_SETTING_` prefix automatically converts to Girder setting via provision script

- **Modified reactdeid service**:
  ```yaml
  VITE_HMR_HOST: ${OAUTH_EXTERNAL_URL:-wsi-deid.pathology.emory.edu}
  ```
  - Now uses centralized variable instead of hardcoded value

#### `devops/nci-dsa-deid/provision.yaml`
- **Added setting**:
  ```yaml
  oauth.external_url: "https://wsi-deid.pathology.emory.edu"
  ```
  - Ensures setting is initialized on first deployment
  - Can be overridden by environment variable

### 3. Environment Templates

#### `example.env`
- **Added**:
  ```bash
  OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
  ```
  - Documents the new environment variable
  - Provides example for deployments

### 4. Documentation

#### `docs/OAUTH_CONFIGURATION.md` (NEW)
- Complete technical documentation
- Explains the problem and solution
- Details configuration flow
- Lists all files changed
- Provides troubleshooting guide
- Includes examples for other OAuth providers

#### `docs/OAUTH_MIGRATION_GUIDE.md` (NEW)
- Step-by-step migration guide for IT
- Environment-specific examples
- Verification procedures
- Troubleshooting section
- Production deployment checklist
- Rollback instructions

#### `README.md`
- Added "Configuration" section
- Links to OAuth documentation
- Highlights requirement for production deployments

## How It Works

### Configuration Flow

```
┌─────────────────────────────────────┐
│  OAUTH_EXTERNAL_URL (env variable)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  DSA_SETTING_oauth.external_url     │
│  (Docker env variable)              │
└──────────────┬──────────────────────┘
               │
               ▼ (provision.py: merge_environ_opts)
┌─────────────────────────────────────┐
│  oauth.external_url                 │
│  (Girder setting in database)       │
└──────────────┬──────────────────────┘
               │
               ▼ (Setting().get())
┌─────────────────────────────────────┐
│  OAuth Providers (UNA, etc.)        │
│  Construct redirect URIs            │
└─────────────────────────────────────┘
```

### Fallback Chain

The UNA provider has multiple fallbacks to ensure OAuth works even if not properly configured:

1. **Primary**: `Setting().get(PluginSettings.EXTERNAL_URL)` - From Girder database
2. **Fallback 1**: `os.environ.get('OAUTH_EXTERNAL_URL')` - Direct environment variable
3. **Fallback 2**: Hardcoded `https://wsi-deid.pathology.emory.edu` (backward compatibility)

Each fallback level logs a message, making it easy to debug configuration issues.

## Benefits

1. **Single Source of Truth**: One environment variable controls all OAuth redirect URLs
2. **Environment Agnostic**: Same code works in dev, staging, and production
3. **Easy Deployment**: IT only needs to set `OAUTH_EXTERNAL_URL`
4. **No Code Changes**: Different environments don't require code modifications
5. **Backward Compatible**: Falls back gracefully if not configured
6. **Visible Configuration**: Setting visible in Girder admin interface
7. **Well Documented**: Comprehensive guides for both developers and IT

## Testing Verification

### Local Development
```bash
# Set environment variable
export OAUTH_EXTERNAL_URL="http://localhost:8090"

# Start services
docker-compose up -d

# Verify
docker-compose logs girder | grep "oauth.external_url"
```

### Production Deployment
```bash
# In .env file
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"

# Deploy
docker-compose up -d

# Verify
docker-compose exec girder python -c "from girder.models.setting import Setting; from girder_oauth.settings import PluginSettings; print(Setting().get(PluginSettings.EXTERNAL_URL))"
```

### OAuth Flow Test
1. Navigate to deployment URL
2. Click "Login with UNA"
3. Check browser console for OAuth redirect URL
4. Should see: `redirect_uri=https://your-domain.example.com/dsa/api/v1/oauth/una/callback`

## Files Modified

### Code Changes
- `plugins/oauth/girder_oauth/settings.py` (added setting constant)
- `plugins/oauth/girder_oauth/providers/una.py` (refactored to use setting)

### Configuration Changes
- `devops/nci-dsa-deid/docker-compose.yml` (added env variables)
- `devops/nci-dsa-deid/provision.yaml` (added setting)
- `example.env` (added documentation)

### Documentation Added
- `docs/OAUTH_CONFIGURATION.md` (technical guide)
- `docs/OAUTH_MIGRATION_GUIDE.md` (IT deployment guide)
- `README.md` (updated with configuration section)

## Backward Compatibility

All changes maintain backward compatibility:

- If `OAUTH_EXTERNAL_URL` is not set, system uses hardcoded fallback
- Existing deployments continue to work without changes
- Migration is optional but recommended for multi-environment setups
- No breaking changes to OAuth providers
- No changes to OAuth callback URL format

## Next Steps for IT

1. Review [docs/OAUTH_MIGRATION_GUIDE.md](OAUTH_MIGRATION_GUIDE.md)
2. Set `OAUTH_EXTERNAL_URL` in deployment environments
3. Test OAuth login after deployment
4. Monitor logs for any OAuth-related warnings

## Future Enhancements

If needed, the same pattern can be applied to other OAuth providers:

- Google OAuth
- GitHub OAuth  
- Microsoft OAuth
- Globus OAuth
- etc.

Simply update each provider to read from `PluginSettings.EXTERNAL_URL` instead of using hardcoded domains.

## Support

For issues or questions:
- Check logs: `docker-compose logs girder | grep oauth`
- Review troubleshooting sections in documentation
- Contact development team with specific error messages
