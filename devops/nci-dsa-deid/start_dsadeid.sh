#export DOCKER_DEFAULT_PLATFORM=linux/amd64

DSA_USER=$(id -u):$(id -g) docker compose down

DSA_USER=$(id -u):$(id -g) DSA_PORT=8080 docker compose up  -d
