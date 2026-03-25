# OAuth Centralization - Testing & Deployment Checklist

## Pre-Deployment Checklist

### Code Review
- [x] Added `EXTERNAL_URL` setting to `plugins/oauth/girder_oauth/settings.py`
- [x] Updated `una.py` provider to use centralized setting
- [x] Added environment variable to `docker-compose.yml`
- [x] Added default value to `provision.yaml`
- [x] Updated `example.env` with documentation
- [x] Created technical documentation
- [x] Created IT migration guide
- [x] Updated README.md

### Backward Compatibility
- [x] Fallback chain implemented (Setting → Env Var → Hardcoded)
- [x] No breaking changes to OAuth providers
- [x] Existing deployments continue to work

## Local Development Testing

### Setup
- [ ] Pull latest code: `git pull`
- [ ] Create/update `.env` file: `cp example.env .env`
- [ ] Set `OAUTH_EXTERNAL_URL` in `.env`:
  ```bash
  OAUTH_EXTERNAL_URL="http://localhost:8090"
  ```

### Container Build & Start
- [ ] Build containers: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Check all containers running: `docker-compose ps`

### Verification
- [ ] Check environment variable is set:
  ```bash
  docker-compose exec girder printenv | grep OAUTH
  ```
  Expected: `OAUTH_EXTERNAL_URL=http://localhost:8090`

- [ ] Check Girder setting:
  ```bash
  docker-compose logs girder | grep "oauth.external_url"
  ```
  Expected: `Setting oauth.external_url to 'http://localhost:8090'`

- [ ] Check setting in database:
  ```bash
  docker-compose exec girder python -c "from girder.models.setting import Setting; from girder_oauth.settings import PluginSettings; print('oauth.external_url:', Setting().get(PluginSettings.EXTERNAL_URL))"
  ```

### OAuth Flow Testing
- [ ] Navigate to http://localhost:8090
- [ ] Open browser developer console (F12)
- [ ] Click "Login with UNA"
- [ ] Check console for OAuth redirect URL
- [ ] Verify redirect_uri parameter matches your domain:
  ```
  redirect_uri=http://localhost:8090/dsa/api/v1/oauth/una/callback
  ```
- [ ] Complete OAuth login flow
- [ ] Verify successful authentication

### Log Inspection
- [ ] Check for OAuth debug messages:
  ```bash
  docker-compose logs girder | grep -i "oauth\|redirect"
  ```
- [ ] Look for "Using centralized external URL setting" message
- [ ] Verify no "Using hardcoded fallback" warnings (unless intended)

## Staging Environment Testing

### Preparation
- [ ] Ensure staging environment exists
- [ ] Set `OAUTH_EXTERNAL_URL` for staging:
  ```bash
  OAUTH_EXTERNAL_URL="https://staging-wsi-deid.pathology.emory.edu"
  ```

### Deployment
- [ ] Deploy to staging
- [ ] Verify environment variable: `docker-compose exec girder printenv | grep OAUTH`
- [ ] Check logs: `docker-compose logs girder | grep oauth.external_url`
- [ ] Test OAuth login with staging URL
- [ ] Verify OAuth callback URL uses staging domain

### Validation
- [ ] Login successful
- [ ] No redirect_uri mismatch errors
- [ ] Check Girder admin interface for `oauth.external_url` setting
- [ ] Verify value matches staging domain

## Production Deployment Checklist

### Pre-Deployment
- [ ] Review [OAUTH_MIGRATION_GUIDE.md](OAUTH_MIGRATION_GUIDE.md)
- [ ] Coordinate with IT team
- [ ] Verify OAuth callback URL registered with UNA:
  ```
  https://wsi-deid.pathology.emory.edu/dsa/api/v1/oauth/una/callback
  ```
- [ ] Create production `.env` file with:
  ```bash
  OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
  ```

### Deployment Steps
- [ ] Pull latest code: `git pull`
- [ ] Backup current deployment (if applicable)
- [ ] Build new images: `docker-compose build`
- [ ] Stop current services: `docker-compose down`
- [ ] Start new services: `docker-compose up -d`
- [ ] Wait for services to be healthy: `docker-compose ps`

### Post-Deployment Verification
- [ ] Check environment variable:
  ```bash
  docker-compose exec girder printenv | grep OAUTH
  ```

- [ ] Check Girder setting in database:
  ```bash
  docker-compose exec girder python -c "from girder.models.setting import Setting; from girder_oauth.settings import PluginSettings; print('oauth.external_url:', Setting().get(PluginSettings.EXTERNAL_URL))"
  ```

- [ ] Review Girder startup logs:
  ```bash
  docker-compose logs girder | tail -200
  ```

- [ ] Look for setting confirmation:
  ```bash
  docker-compose logs girder | grep "oauth.external_url"
  ```

### Functional Testing
- [ ] Navigate to production URL
- [ ] Click "Login with UNA"
- [ ] Open browser console, verify redirect_uri parameter
- [ ] Complete OAuth login
- [ ] Verify successful authentication
- [ ] Test logout
- [ ] Test re-login

### Monitoring (First 24 Hours)
- [ ] Monitor application logs: `docker-compose logs -f`
- [ ] Watch for OAuth-related errors
- [ ] Check error rates (if monitoring available)
- [ ] Verify user reports of successful logins
- [ ] Check for "redirect_uri mismatch" errors

## Rollback Plan

If issues occur:

### Quick Rollback (Emergency)
- [ ] Stop new deployment: `docker-compose down`
- [ ] Restore from backup (if available)
- [ ] Start previous version
- [ ] Verify OAuth working

### Issue Investigation
- [ ] Capture logs: `docker-compose logs girder > girder-error.log`
- [ ] Check environment: `docker-compose config > config.yaml`
- [ ] Verify OAuth setting: Check Girder admin interface
- [ ] Review error messages in logs

### Rollback with Fix
- [ ] Identify the issue (see Troubleshooting below)
- [ ] Apply fix (usually environment variable correction)
- [ ] Redeploy: `docker-compose up -d`
- [ ] Retest OAuth flow

## Troubleshooting Common Issues

### Issue: "redirect_uri mismatch" Error

**Symptoms**: OAuth fails with error about redirect URI not matching

**Check**:
- [ ] Verify `OAUTH_EXTERNAL_URL` matches deployment domain
- [ ] Check OAuth callback URL registered with UNA
- [ ] Review browser console for actual redirect_uri used
- [ ] Compare against registered callback URL

**Fix**:
```bash
# Update environment variable
export OAUTH_EXTERNAL_URL="https://correct-domain.example.com"

# Or update .env file
echo 'OAUTH_EXTERNAL_URL="https://correct-domain.example.com"' >> .env

# Restart
docker-compose restart girder
```

### Issue: Environment Variable Not Set

**Symptoms**: Logs show "Using hardcoded fallback" warning

**Check**:
- [ ] Verify `.env` file exists
- [ ] Check variable in `.env`: `cat .env | grep OAUTH`
- [ ] Verify docker-compose uses env_file or has variable in environment section

**Fix**:
```bash
# Add to .env
echo 'OAUTH_EXTERNAL_URL="https://your-domain.example.com"' >> .env

# Recreate container
docker-compose up -d --force-recreate girder
```

### Issue: Old Setting Value Persists

**Symptoms**: Girder uses old domain despite new environment variable

**Check**:
- [ ] Check database setting: 
  ```bash
  docker-compose exec girder python -c "from girder.models.setting import Setting; print(Setting().get('oauth.external_url'))"
  ```

**Fix**:
```bash
# Force update setting
docker-compose exec girder python -c "from girder.models.setting import Setting; Setting().set('oauth.external_url', 'https://your-domain.example.com')"

# Or clear and restart
docker-compose exec girder python -c "from girder.models.setting import Setting; Setting().unset('oauth.external_url')"
docker-compose restart girder
```

### Issue: Containers Won't Start

**Symptoms**: `docker-compose up` fails or containers exit immediately

**Check**:
- [ ] Check syntax in `docker-compose.yml`
- [ ] Verify `.env` file format (no spaces around `=`)
- [ ] Check Docker logs: `docker-compose logs`

**Fix**:
```bash
# Validate docker-compose file
docker-compose config

# Check for syntax errors in output
# Fix any issues in docker-compose.yml or .env
# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

## Multiple Environment Management

### Development
```bash
# .env.development
OAUTH_EXTERNAL_URL="http://localhost:8090"
```

### Staging
```bash
# .env.staging
OAUTH_EXTERNAL_URL="https://staging-wsi-deid.pathology.emory.edu"
```

### Production
```bash
# .env.production
OAUTH_EXTERNAL_URL="https://wsi-deid.pathology.emory.edu"
```

**Deploy to specific environment**:
```bash
# Specify env file
docker-compose --env-file .env.production up -d
```

## Sign-Off

### Development Team
- [ ] Code changes reviewed
- [ ] Local testing completed
- [ ] Documentation reviewed
- [ ] Staging deployment successful

### IT/DevOps Team
- [ ] Migration guide reviewed
- [ ] Environment variables configured
- [ ] Production deployment completed
- [ ] Post-deployment verification passed
- [ ] Monitoring in place

### Project Manager
- [ ] All teams signed off
- [ ] Users notified of deployment
- [ ] Support team briefed
- [ ] Documentation accessible

## Support Contacts

- **Technical Issues**: Development team
- **Deployment Issues**: IT/DevOps team
- **OAuth Provider Issues**: UNA administrator
- **Documentation**: [docs/OAUTH_CONFIGURATION.md](OAUTH_CONFIGURATION.md)
