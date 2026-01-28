from girder.api.rest import getApiUrl
from .base import ProviderBase, ProviderException
from girder.models.setting import Setting
from ..settings import PluginSettings
from urllib.parse import quote, urlencode


class Una(ProviderBase):
    _AUTH_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/authorize"
    _TOKEN_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/oidc/token"
    _API_USER_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/me"

    def __init__(self, redirectUri, clientId=None, clientSecret=None):
        # Override __init__ to ensure redirectUri is always the correct external URL
        # This ensures consistency between authorization request and token exchange
        print(f"Una.__init__() called with redirectUri: '{redirectUri}'")
        redirectUri = self._normalizeRedirectUri(redirectUri)
        print(f"Una.__init__() normalized redirectUri to: '{redirectUri}'")
        super().__init__(redirectUri, clientId, clientSecret)

    @classmethod
    def _normalizeRedirectUri(cls, redirectUri):
        """
        Normalize the redirect URI to ensure it uses the external domain,
        not an internal Docker hostname. This ensures consistency between
        the authorization request and token exchange.
        
        Note: cherrypy.url() may return just the base API URL (e.g., http://docker-dsa/api/v1)
        or the full callback URL. This function handles both cases.
        """
        if not redirectUri:
            return redirectUri
        
        print(f"_normalizeRedirectUri() input: '{redirectUri}'")
        
        # If it's already using the correct external domain, return as-is
        if "wsi-deid.pathology.emory.edu" in redirectUri:
            print(f"Redirect URI already uses external domain, returning as-is")
            return redirectUri
        
        # Parse the URI
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(redirectUri)
        
        # Check if it's an internal Docker hostname or localhost
        needs_normalization = (
            "docker-" in parsed.netloc or 
            "girder" in parsed.netloc or 
            "localhost" in parsed.netloc or 
            ":8090" in parsed.netloc or
            not parsed.netloc  # Might be a relative path
        )
        
        if needs_normalization:
            # Determine the path - ensure it includes /dsa prefix
            if parsed.path == "/api/v1" or parsed.path == "/dsa/api/v1" or not parsed.path or parsed.path == "/":
                # cherrypy.url() returned just the base URL, need to construct full callback URL
                path = "/dsa/api/v1/oauth/una/callback"
            elif parsed.path.startswith("/api/v1/oauth/una/callback"):
                # Path is missing /dsa prefix, add it
                path = "/dsa" + parsed.path
            elif parsed.path.startswith("/dsa/api/v1/oauth/una/callback"):
                # Path already has /dsa, keep it
                path = parsed.path
            else:
                # It's some other path, ensure it has /dsa if it's an API path
                if parsed.path.startswith("/api/v1"):
                    path = "/dsa" + parsed.path
                else:
                    path = parsed.path
            
            # Replace with external domain
            normalized = urlunparse((
                "https",  # Always use https for external
                "wsi-deid.pathology.emory.edu",
                path,  # Use the determined path
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            print(f"Normalized redirect URI from '{redirectUri}' to '{normalized}'")
            return normalized
        
        # If it doesn't need normalization but doesn't have the external domain,
        # it might be a relative path or something unexpected
        if not parsed.netloc:
            # Relative path - construct full URL
            path = parsed.path if parsed.path else "/dsa/api/v1/oauth/una/callback"
            normalized = urlunparse((
                "https",
                "wsi-deid.pathology.emory.edu",
                path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            print(f"Constructed full URL from relative path: '{redirectUri}' -> '{normalized}'")
            return normalized
        
        print(f"Redirect URI doesn't need normalization: '{redirectUri}'")
        return redirectUri

    def getClientIdSetting(self):
        return Setting().get("oauth.una_client_id")

    def getClientSecretSetting(self):
        return Setting().get("oauth.una_client_secret")

    @classmethod
    def getUrl(cls, state):
        # Get settings directly from the Setting model
        clientId = Setting().get(PluginSettings.UNA_CLIENT_ID)
        if not clientId:
            raise Exception("No UNA client ID setting is present.")

        # Try to get API URL - getApiUrl() should work if headers are set correctly
        apiUrl = None
        try:
            apiUrl = getApiUrl()
        except Exception as e:
            print(f"getApiUrl() failed: {e}")
            apiUrl = None
        
        # Check if we got an internal Docker hostname (indicates forwarded headers aren't working)
        # or if getApiUrl() failed
        if (not apiUrl or 
            "docker-" in apiUrl or 
            apiUrl.startswith("http://girder") or 
            apiUrl.startswith("https://girder") or
            "localhost" in apiUrl or
            ":8090" in apiUrl):
            # Fallback: construct from headers directly
            import cherrypy
            forwarded_host = ""
            forwarded_proto = "https"
            host = ""
            referer = ""
            
            try:
                # Try to get headers from the current request
                headers = cherrypy.request.headers
                forwarded_host = headers.get("X-Forwarded-Host", "")
                forwarded_proto = headers.get("X-Forwarded-Proto", "https")
                host = headers.get("Host", "")
                referer = headers.get("Referer", "")
                
                print(f"Debug OAuth headers - X-Forwarded-Host: '{forwarded_host}', X-Forwarded-Proto: '{forwarded_proto}', Host: '{host}', Referer: '{referer}'")
            except (AttributeError, Exception) as e:
                print(f"Could not access request headers: {e}")
            
            # Prefer X-Forwarded-Host if available
            if forwarded_host:
                # Remove port if present (X-Forwarded-Host might include port)
                if ":" in forwarded_host:
                    forwarded_host = forwarded_host.split(":")[0]
                apiUrl = f"{forwarded_proto}://{forwarded_host}/dsa/api/v1"
                print(f"Using X-Forwarded-Host to construct API URL: {apiUrl}")
            elif host and not ("docker-" in host or "localhost" in host or ":8090" in host or "girder" in host):
                # Use Host header if it looks like an external domain
                apiUrl = f"{forwarded_proto}://{host}/dsa/api/v1"
                print(f"Using Host header to construct API URL: {apiUrl}")
            elif referer:
                # Try to get from referer
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                if parsed.netloc and not ("docker-" in parsed.netloc or "localhost" in parsed.netloc):
                    apiUrl = f"{parsed.scheme}://{parsed.netloc}/dsa/api/v1"
                    print(f"Using Referer to construct API URL: {apiUrl}")
            
            # Final fallback: use hardcoded external domain
            # This ensures OAuth always works even if headers aren't set correctly
            if not apiUrl or "docker-" in apiUrl or "localhost" in apiUrl or ":8090" in apiUrl:
                apiUrl = "https://wsi-deid.pathology.emory.edu/dsa/api/v1"
                print(f"Using hardcoded fallback API URL: {apiUrl}")

        redirectUri = "/".join((apiUrl, "oauth", "una", "callback"))
        print(f"getUrl() - Final OAuth redirect URI for authorization request: '{redirectUri}'")
        # URL encode the parameters
        params = {
            "client_id": clientId,
            "state": state,
            "response_type": "code",
            "redirect_uri": redirectUri,
            "scope": "openid profile email",
        }
        print(f"getUrl() - Sending authorization request with redirect_uri: '{redirectUri}'")

        query_string = urlencode(params)
        return f"{cls._AUTH_URL}?{query_string}"

    def getToken(self, code):
        print(f"getToken() called with redirect_uri: '{self.redirectUri}'")
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "redirect_uri": self.redirectUri,
        }
        print(f"Sending token request with redirect_uri: '{self.redirectUri}'")
        resp = self._getJson(method="POST", url=self._TOKEN_URL, data=params)
        if "error" in resp:
            raise ProviderException(
                "Got error from token endpoint: %s" % resp.get("error", "Unknown")
            )
        return resp

    def getUser(self, token):
        headers = {"Authorization": "Bearer {}".format(token["access_token"])}

        # Get user info from UNA API
        resp = self._getJson(method="GET", url=self._API_USER_URL, headers=headers)

        # Get username and clean it up
        userName = resp.get("username", "")
        # If it looks like an email, extract just the username part
        if "@" in userName:
            userName = userName.split("@")[0]
        # If it has a domain suffix but no @, remove the domain part
        elif "." in userName and not userName.startswith("."):
            # Take everything before the first dot
            userName = userName.split(".")[0]

        # If there's no email, create a proper email from username
        email = resp.get("email")
        if not email and userName:
            email = f"{userName}@ncats.nih.gov"
        elif not email:
            email = "unknown@ncats.nih.gov"

        # Try to get a unique identifier - prefer 'id' but fall back to 'sub' (OIDC standard) or username
        oauthId = resp.get("id") or resp.get("sub") or resp.get("username")
        if not oauthId:
            raise ProviderException("UNA API did not return a unique user identifier")
        oauthId = str(oauthId)
        
        print("oauthId", oauthId, "email", email, "userName", userName)
        # Try different possible field names for first and last name
        firstName = resp.get("firstName") or resp.get("first_name") or resp.get("given_name") or resp.get("name", "").split()[0] if resp.get("name") else ""
        lastName = resp.get("lastName") or resp.get("last_name") or resp.get("family_name") or resp.get("name", "").split()[-1] if resp.get("name") else ""
        
        # If still empty, use cleaned username as fallback
        if not firstName and not lastName:
            firstName = userName
            lastName = userName
        elif not firstName:
            firstName = lastName
        elif not lastName:
            lastName = firstName

        return self._createOrReuseUser(oauthId, email, firstName, lastName, userName)
