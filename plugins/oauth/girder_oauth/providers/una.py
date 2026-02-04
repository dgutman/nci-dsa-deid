from girder.api.rest import getApiUrl
from .base import ProviderBase, ProviderException
from girder.models.setting import Setting
from ..settings import PluginSettings
from urllib.parse import quote, urlencode, urlparse, urlunparse


def _is_internal_host(netloc):
    """True if this is an internal Docker/localhost host that should be replaced."""
    if not netloc:
        return True
    return (
        "docker-" in netloc
        or "girder" in netloc
        or "localhost" in netloc
        or ":8090" in netloc
        or netloc.startswith("127.")
    )


def _get_external_base_from_request():
    """
    Get the external (scheme + host) from the current request headers.
    Used so redirect_uri is consistent for both auth and token steps (proxy-safe).
    """
    try:
        import cherrypy
        headers = cherrypy.request.headers
        forwarded_host = (headers.get("X-Forwarded-Host") or "").strip()
        forwarded_proto = (headers.get("X-Forwarded-Proto") or "https").strip().lower()
        host = (headers.get("Host") or "").strip()
        if ":" in forwarded_host:
            forwarded_host = forwarded_host.split(":")[0]
        if ":" in host:
            host = host.split(":")[0]
        if forwarded_host and not _is_internal_host(forwarded_host):
            return f"{forwarded_proto}://{forwarded_host}"
        if host and not _is_internal_host(host):
            return f"{forwarded_proto}://{host}"
    except Exception:
        pass
    return None


class Una(ProviderBase):
    _AUTH_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/authorize"
    _TOKEN_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/oidc/token"
    _API_USER_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/me"

    def __init__(self, redirectUri, clientId=None, clientSecret=None):
        # Ensure redirectUri uses the same external host as the request (avoids redirect_uri mismatch)
        print(f"Una.__init__() called with redirectUri: '{redirectUri}'")
        redirectUri = self._normalizeRedirectUri(redirectUri)
        print(f"Una.__init__() normalized redirectUri to: '{redirectUri}'")
        super().__init__(redirectUri, clientId, clientSecret)

    @classmethod
    def _normalizeRedirectUri(cls, redirectUri):
        """
        Use the external domain from the current request (X-Forwarded-Host / Host),
        not an internal Docker hostname. Keeps redirect_uri identical for auth and token exchange.
        Works for any public host (e.g. wsi-deid.cancer.gov or wsi-deid.pathology.emory.edu).
        """
        if not redirectUri:
            return redirectUri

        print(f"_normalizeRedirectUri() input: '{redirectUri}'")
        parsed = urlparse(redirectUri)

        # If it already has an external (non-internal) host, return as-is so we don't change cancer.gov -> emory.edu
        if parsed.netloc and not _is_internal_host(parsed.netloc):
            print(f"Redirect URI already has external host, returning as-is")
            return redirectUri

        # Need to replace internal host or relative path with current request's external base
        external_base = _get_external_base_from_request()
        if not external_base:
            print(f"No external base from request, returning redirectUri as-is")
            return redirectUri

        if parsed.path == "/api/v1" or parsed.path == "/dsa/api/v1" or not parsed.path or parsed.path == "/":
            path = "/dsa/api/v1/oauth/una/callback"
        elif parsed.path.startswith("/api/v1/oauth/una/callback"):
            path = "/dsa" + parsed.path
        elif parsed.path.startswith("/dsa/api/v1/oauth/una/callback"):
            path = parsed.path
        else:
            path = "/dsa" + parsed.path if parsed.path.startswith("/api/v1") else (parsed.path or "/dsa/api/v1/oauth/una/callback")

        base = urlparse(external_base)
        normalized = urlunparse((base.scheme, base.netloc, path, parsed.params, parsed.query, parsed.fragment))
        print(f"Normalized redirect URI from '{redirectUri}' to '{normalized}'")
        return normalized

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
        
        # If getApiUrl() returned an internal host or failed, build from request headers
        # so redirect_uri matches the host the user is on (e.g. wsi-deid.cancer.gov or wsi-deid.pathology.emory.edu)
        if not apiUrl or _is_internal_host(urlparse(apiUrl).netloc) or "docker-" in apiUrl or "girder" in apiUrl or "localhost" in apiUrl or ":8090" in apiUrl:
            external_base = _get_external_base_from_request()
            if external_base:
                apiUrl = f"{external_base}/dsa/api/v1"
                print(f"Using request headers to construct API URL: {apiUrl}")
            else:
                try:
                    import cherrypy
                    referer = (cherrypy.request.headers.get("Referer") or "").strip()
                    if referer:
                        pr = urlparse(referer)
                        if pr.netloc and not _is_internal_host(pr.netloc):
                            apiUrl = f"{pr.scheme}://{pr.netloc}/dsa/api/v1"
                            print(f"Using Referer to construct API URL: {apiUrl}")
                except Exception:
                    pass
            if not apiUrl or _is_internal_host(urlparse(apiUrl).netloc):
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
