#docker build --no-cache -t nci_dsa_deid .
#docker build -t nci_dsa_deid -f devops/nci-dsa-deid/Dockerfile .
docker build -f devops/nci-dsa-deid/Dockerfile -t dagutman/nci-dsa-deid:latest .
# docker tag nci_dsa_deid dagutman/nci-dsa-deid


docker build -t dashncidsadeidapp --platform=linux/amd64 .
docker tag dashncidsadeidapp dagutman/dashncidsadeidapp