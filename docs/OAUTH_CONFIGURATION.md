# OAuth Redirect URL Configuration

## Overview

This document explains how OAuth redirect URLs are centrally configured in the NCI-DSA-DEID application to avoid hardcoded values and deployment issues.

## Problem

Previously, the OAuth redirect URL was hardcoded in multiple places:
- `plugins/oauth/girder_oauth/providers/una.py` (hardcoded domain)
- `devops/nci-dsa-deid/docker-compose.yml` (VITE_HMR_HOST)

This caused deployment failures when IT tried to deploy to different environments, as the hardcoded values didn't match the actual deployment domain.

## Solution

We've centralized the OAuth redirect URL configuration using a single environment variable that flows through the entire stack:

### 1. Environment Variable

**`OAUTH_EXTERNAL_URL`** - The public-facing URL of your deployment

Example: `https://wsi-deid.pathology.emory.edu`

### 2. Configuration Flow

```
OAUTH_EXTERNAL_URL (environment variable)
    ↓
DSA_SETTING_oauth.external_url (Girder environment variable)
    ↓
oauth.external_url (Girder setting in database)
    ↓
Used by OAuth providers (UNA, etc.)
```

### 3. Files Changed

#### a. OAuth Plugin Settings (`plugins/oauth/girder_oauth/settings.py`)
- Added `EXTERNAL_URL = "oauth.external_url"` setting constant
- Registered the setting with validators and defaults

#### b. UNA OAuth Provider (`plugins/oauth/girder_oauth/providers/una.py`)
- Modified `_normalizeRedirectUri()` to read from settings or environment variable
- Modified `getUrl()` to use the centralized external URL
- Maintains backward compatibility with hardcoded fallback

#### c. Docker Compose (`devops/nci-dsa-deid/docker-compose.yml`)
- Added `DSA_SETTING_oauth.external_url` environment variable to girder service
- Updated `VITE_HMR_HOST` in reactdeid service to use `${OAUTH_EXTERNAL_URL}`

#### d. Provision Config (`devops/nci-dsa-deid/provision.yaml`)
- Added `oauth.external_url` setting with default value
- This ensures the setting is initialized on first deployment

#### e. Environment Template (`example.env`)
- Added `OAUTH_EXTERNAL_URL` with documentation

## Usage

### For Development

1. Set the environment variable in your `.env` file:
   ```bash
   OAUTH_EXTERNAL_URL="https://your-domain.example.com"
   ```

2. Restart the stack:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### For Production Deployment

Your IT team should set `OAUTH_EXTERNAL_URL` in the environment where the containers run:

```bash
export OAUTH_EXTERNAL_URL="https://production-domain.example.com"
```

Or in a `.env` file:
```bash
OAUTH_EXTERNAL_URL="https://production-domain.example.com"
```

### Verification

To verify the setting is applied:

1. Check Girder logs during startup:
   ```bash
   docker-compose logs girder | grep "oauth.external_url"
   ```

2. Check the OAuth authorization URL in the browser console when logging in

3. Verify in Girder admin interface:
   - Login as admin
   - Go to Admin Console → System Configuration
   - Look for `oauth.external_url` setting

## How It Works

### Environment Variable Processing

The provision script (`provision.py`) has a special function `merge_environ_opts()` that:

1. Looks for environment variables starting with `DSA_SETTING_`
2. Strips the `DSA_SETTING_` prefix
3. Sets the remaining part as a Girder setting

Example:
```
DSA_SETTING_oauth.external_url=https://example.com
    ↓
Setting().set("oauth.external_url", "https://example.com")
```

### OAuth Provider Usage

The UNA OAuth provider (`una.py`) uses this setting with multiple fallbacks:

1. **Primary**: `Setting().get(PluginSettings.EXTERNAL_URL)` - From Girder database
2. **Fallback 1**: `os.environ.get('OAUTH_EXTERNAL_URL')` - Direct environment variable
3. **Fallback 2**: Hardcoded value for backward compatibility

This ensures OAuth continues to work even if the setting isn't properly configured, while warning in the logs.

## Benefits

1. **Single Source of Truth**: One environment variable controls all OAuth redirect URLs
2. **Easy Deployment**: IT can set `OAUTH_EXTERNAL_URL` for any environment
3. **No Code Changes**: Different environments don't require code modifications
4. **Backward Compatible**: Falls back to hardcoded values if not configured
5. **Visible Configuration**: Setting is visible in Girder admin interface

## Troubleshooting

### OAuth fails with "redirect_uri mismatch"

1. Check the environment variable is set:
   ```bash
   docker-compose exec girder printenv | grep OAUTH
   ```

2. Check Girder setting:
   ```bash
   docker-compose exec girder python -c "from girder.models.setting import Setting; from girder_oauth.settings import PluginSettings; print(Setting().get(PluginSettings.EXTERNAL_URL))"
   ```

3. Check the logs for OAuth debug messages:
   ```bash
   docker-compose logs girder | grep "OAuth\|redirect"
   ```

### Setting not taking effect

1. Ensure the environment variable is in `docker-compose.yml` girder service
2. Restart the girder container: `docker-compose restart girder`
3. Check if provision script ran: `docker-compose logs girder | grep provision`

## For Other OAuth Providers

If you need to add support for other OAuth providers (Google, GitHub, etc.), follow the same pattern:

1. Read the external URL from `Setting().get(PluginSettings.EXTERNAL_URL)`
2. Parse it to extract the domain
3. Construct the redirect URI using that domain
4. Add fallback to `os.environ.get('OAUTH_EXTERNAL_URL')` if setting is not available

Example:
```python
from girder.models.setting import Setting
from ..settings import PluginSettings
import os

externalUrl = Setting().get(PluginSettings.EXTERNAL_URL)
if not externalUrl:
    externalUrl = os.environ.get('OAUTH_EXTERNAL_URL', '')
```

## Related Files

- `plugins/oauth/girder_oauth/settings.py` - Setting definition
- `plugins/oauth/girder_oauth/providers/una.py` - UNA OAuth provider
- `devops/nci-dsa-deid/docker-compose.yml` - Docker configuration
- `devops/nci-dsa-deid/provision.yaml` - Girder provisioning config
- `devops/nci-dsa-deid/provision.py` - Provisioning script
- `example.env` - Environment variable template
