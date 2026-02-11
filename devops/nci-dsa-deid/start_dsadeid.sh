# Optional: set OAuth UNA callback URL when proxy headers are wrong. Uncomment and set for your host.
# export UNA_OAUTH_REDIRECT_URI="https://wsi-deid.cancer.gov/dsa/api/v1/oauth/una/callback"
export UNA_OAUTH_REDIRECT_URI="${UNA_OAUTH_REDIRECT_URI:-}"

DSA_USER=$(id -u):$(id -g) docker compose down

DSA_USER=$(id -u):$(id -g) docker compose up -d
