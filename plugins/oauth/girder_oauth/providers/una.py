from girder.api.rest import getApiUrl
from .base import ProviderBase, ProviderException
from girder.models.setting import Setting
from ..settings import PluginSettings
from urllib.parse import quote, urlencode


class Una(ProviderBase):
    _AUTH_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/authorize"
    _TOKEN_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/oidc/token"
    _API_USER_URL = "https://auth.ncats.nih.gov/_api/v2/auth/NCI-DMAP/me"

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

        redirectUri = "/".join((getApiUrl(), "oauth", "una", "callback"))

        # URL encode the parameters
        params = {
            "client_id": clientId,
            "state": state,
            "response_type": "code",
            "redirect_uri": redirectUri,
            "scope": "openid profile email",
        }

        query_string = urlencode(params)
        return f"{cls._AUTH_URL}?{query_string}"

    def getToken(self, code):
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "redirect_uri": self.redirectUri,
        }
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

        # Debug: Print the response to see what fields are available
        print("UNA API Response:", resp)

        # If there's no email, fall back to username@domain
        email = resp.get("email", "{}@ncats.nih.gov".format(resp.get("username", "")))

        oauthId = str(resp.get("id", ""))
        
        # Try different possible field names for first and last name
        firstName = resp.get("firstName") or resp.get("first_name") or resp.get("given_name") or resp.get("name", "").split()[0] if resp.get("name") else ""
        lastName = resp.get("lastName") or resp.get("last_name") or resp.get("family_name") or resp.get("name", "").split()[-1] if resp.get("name") else ""
        
        # If still empty, use username as fallback
        if not firstName and not lastName:
            userName = resp.get("username", "")
            firstName = userName
            lastName = userName
        elif not firstName:
            firstName = lastName
        elif not lastName:
            lastName = firstName
            
        userName = resp.get("username", "")

        return self._createOrReuseUser(oauthId, email, firstName, lastName, userName)
