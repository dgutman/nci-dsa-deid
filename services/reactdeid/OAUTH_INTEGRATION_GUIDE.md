# OAuth Integration Guide for dsaAuthStore/dsaAuthenticator

This document outlines the changes needed to add OAuth provider support (like UNA) to the `dsaAuthStore` and `DsaAuthManager` components in `bdsa-react-components`, so that OAuth logic can be reused across applications instead of being implemented separately in each app.

## Current State

Currently, OAuth support (specifically UNA) is implemented directly in application code:
- `UnaAuthButton.jsx` - Custom component for UNA OAuth flow
- `Layout.jsx` - Manual token extraction from URL and `dsaAuthStore` property manipulation

This approach requires duplicating OAuth logic in every application that needs it.

## Proposed Changes to bdsa-react-components

### 1. Add OAuth Provider Configuration to dsaAuthStore

**Location**: `dsaAuthStore` configuration

**Changes Needed**:
```javascript
// Add to dsaAuthStore config
{
  baseUrl: string,
  oauthProviders?: {
    enabled: boolean,
    providers?: Array<{
      id: string,           // e.g., 'una'
      name: string,         // e.g., 'UNA'
      authUrl: string,      // OAuth authorization URL
      // Optional: custom redirect handler
    }>
  }
}
```

### 2. Add OAuth Methods to dsaAuthStore

**New Methods**:

```javascript
// Get list of available OAuth providers from Girder
dsaAuthStore.getOAuthProviders(): Promise<Array<OAuthProvider>>

// Initiate OAuth flow for a specific provider
dsaAuthStore.initiateOAuth(providerId: string, redirectUrl?: string): Promise<void>

// Handle OAuth callback (extract token from URL and authenticate)
dsaAuthStore.handleOAuthCallback(): Promise<boolean> // Returns true if token was found and processed

// Check if there's a token in the current URL (from OAuth redirect)
dsaAuthStore.hasTokenInUrl(): boolean

// Extract token from URL and authenticate (used by handleOAuthCallback)
dsaAuthStore.authenticateWithToken(token: string, userInfo?: object): Promise<void>
```

### 3. Update DsaAuthManager Component

**New Props**:
```typescript
interface DsaAuthManagerProps {
  // ... existing props ...
  
  // Enable OAuth provider buttons
  showOAuthProviders?: boolean
  
  // Custom OAuth provider renderer (optional)
  renderOAuthProvider?: (provider: OAuthProvider) => ReactNode
  
  // Callback when OAuth flow completes
  onOAuthSuccess?: () => void
  
  // Pre-configure server URL (pre-fill the field)
  defaultServerUrl?: string
  
  // Hide server URL input field if it's always the same (e.g., always connects to same host)
  // When true, the server URL is read from dsaAuthStore config and the field is hidden
  hideServerUrlField?: boolean
}
```

**Behavior Changes**:
- Automatically detect `girderToken` or `token` in URL on mount
- Call `dsaAuthStore.handleOAuthCallback()` if token is present
- Show OAuth provider buttons if `showOAuthProviders={true}`
- Display OAuth providers alongside or instead of username/password form
- If `defaultServerUrl` is provided, pre-fill the server URL field
- If `hideServerUrlField={true}`, hide the server URL input and use the value from `dsaAuthStore` config or `defaultServerUrl`

### 4. OAuth Flow Implementation

**Step 1: Get OAuth Providers**
```javascript
// In dsaAuthStore.getOAuthProviders()
const response = await fetch(`${baseUrl}/api/v1/oauth/provider?list=true`, {
  credentials: 'include'
})
const providers = await response.json()
// Returns: [{ id: 'una', name: 'UNA', url: 'https://auth.ncats.nih.gov/...' }, ...]
```

**Step 2: Initiate OAuth**
```javascript
// In dsaAuthStore.initiateOAuth(providerId, redirectUrl)
const providers = await this.getOAuthProviders()
const provider = providers.find(p => p.id === providerId)
if (!provider) throw new Error(`OAuth provider ${providerId} not found`)

// Redirect to provider's authorization URL
window.location.href = provider.url
```

**Step 3: Handle Callback**
```javascript
// In dsaAuthStore.handleOAuthCallback()
// Called automatically on mount if token is in URL
const urlParams = new URLSearchParams(window.location.search)
const token = urlParams.get('girderToken') || urlParams.get('token')

if (token) {
  // Verify token and get user info
  const user = await fetch(`${this.config.baseUrl}/api/v1/user/me`, {
    headers: { 'Girder-Token': token }
  }).then(r => r.json())
  
  // Authenticate with token
  await this.authenticateWithToken(token, user)
  
  // Clean up URL (remove token parameter)
  const cleanUrl = window.location.pathname + (window.location.hash || '')
  window.history.replaceState({}, document.title, cleanUrl)
  
  return true
}
return false
```

**Step 4: Authenticate with Token**
```javascript
// In dsaAuthStore.authenticateWithToken(token, userInfo)
// This should be the PRIMARY method for token-based auth
// It should:
// 1. Store token in internal state (not just as a property)
// 2. Store user info
// 3. Set isAuthenticated flag
// 4. Trigger all subscribers
// 5. Persist to localStorage (optional, for refresh persistence)

this.token = token
this.userInfo = userInfo || await this.getUserInfo(token)
this.isAuthenticated = true
this.notify() // Notify all subscribers
localStorage.setItem('girderToken', token) // Optional persistence
```

### 5. URL Token Detection

**Automatic Detection**:
- `DsaAuthManager` should check for `girderToken` or `token` in URL on mount
- If found, automatically call `dsaAuthStore.handleOAuthCallback()`
- This eliminates the need for manual token extraction in application code

### 6. Component Usage (After Changes)

**Before (Current)**:
```jsx
// Custom implementation required
<UnaAuthButton />
<DsaAuthManager compact={true} />
```

**After (Proposed)**:
```jsx
// Single component handles both OAuth and local auth
<DsaAuthManager 
  showOAuthProviders={true}
  compact={true}
  onOAuthSuccess={() => {
    // Optional: refresh page or update state
  }}
/>
```

Or if you want separate buttons:
```jsx
<DsaAuthManager 
  showOAuthProviders={true}
  oauthOnly={true}  // Only show OAuth buttons
/>
<DsaAuthManager 
  localOnly={true}  // Only show username/password form
/>
```

## Implementation Checklist

### Phase 1: Core OAuth Support
- [ ] Add `getOAuthProviders()` method to `dsaAuthStore`
- [ ] Add `initiateOAuth(providerId, redirectUrl)` method
- [ ] Add `authenticateWithToken(token, userInfo)` method (PRIMARY method)
- [ ] Add `handleOAuthCallback()` method
- [ ] Add `hasTokenInUrl()` helper method

### Phase 2: Component Integration
- [ ] Update `DsaAuthManager` to detect tokens in URL on mount
- [ ] Add `showOAuthProviders` prop to `DsaAuthManager`
- [ ] Add `defaultServerUrl` prop to pre-fill server URL field
- [ ] Add `hideServerUrlField` prop to hide server URL when it's always the same (e.g., always `/dsa`)
- [ ] Render OAuth provider buttons when enabled
- [ ] Handle OAuth callback automatically

### Phase 3: Configuration
- [ ] Add OAuth provider configuration to store config
- [ ] Support custom redirect URLs
- [ ] Support multiple OAuth providers

### Phase 4: Cleanup
- [ ] Remove manual token extraction from application code
- [ ] Remove custom `UnaAuthButton` components
- [ ] Update documentation

## Benefits

1. **Reusability**: OAuth logic is centralized in `bdsa-react-components`
2. **Consistency**: All apps use the same OAuth flow
3. **Maintainability**: Bug fixes and improvements benefit all apps
4. **Simplicity**: Applications just enable `showOAuthProviders={true}`
5. **Flexibility**: Still supports custom implementations if needed

## Migration Path

1. Implement changes in `bdsa-react-components`
2. Update `dsaAuthStore.authenticateWithToken()` to be the primary token auth method
3. Test with existing applications
4. Migrate applications to use new OAuth support
5. Remove custom OAuth implementations from applications

## Example: Full OAuth Flow

```javascript
// 1. User clicks "Login with UNA"
dsaAuthStore.initiateOAuth('una', window.location.href)

// 2. User is redirected to UNA, authenticates, and is redirected back
// URL: https://app.example.com/?girderToken=abc123

// 3. DsaAuthManager automatically detects token on mount
// Calls: dsaAuthStore.handleOAuthCallback()

// 4. handleOAuthCallback() extracts token, verifies it, and calls authenticateWithToken()
dsaAuthStore.authenticateWithToken('abc123', { login: 'user@example.com', ... })

// 5. authenticateWithToken() updates store state and notifies subscribers
// All components using dsaAuthStore automatically see the user as authenticated

// 6. URL is cleaned up (token parameter removed)
// User is now logged in
```

## Notes

- The `authenticateWithToken()` method is critical - it should properly set internal state, not just properties
- Token should be stored in localStorage for persistence across page refreshes
- URL cleanup should use `history.replaceState()` to avoid adding to browser history
- OAuth providers are fetched from Girder's `/api/v1/oauth/provider?list=true` endpoint
- The redirect URL should be the current page URL (or a configured callback URL)
- **Server URL Field**: When `hideServerUrlField={true}`, the component should read the server URL from `dsaAuthStore.config.baseUrl` or use `defaultServerUrl` prop. This is useful when the app always connects to the same DSA instance (e.g., `/dsa` proxied by nginx). The field should be completely hidden from the UI, not just pre-filled.

