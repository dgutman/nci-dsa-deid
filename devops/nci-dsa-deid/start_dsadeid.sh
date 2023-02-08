DSA_USER=$(id -u):$(id -g) docker compose down

DSA_USER=$(id -u):$(id -g) DSA_PORT=8080 docker compose up  -d
