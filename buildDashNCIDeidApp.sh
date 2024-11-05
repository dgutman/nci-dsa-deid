## App requires a .env file with a DSA_API_URL specifies
docker build -t dashncidsadeidapp --platform=linux/amd64 .
docker tag dashncidsadeidapp dagutman/dashncidsadeidapp
docker stop dashdeid
#docker run -p8050:8050 --platform=linux/amd64 --name dashdeid dagutman/dashncidsadeidapp -d
