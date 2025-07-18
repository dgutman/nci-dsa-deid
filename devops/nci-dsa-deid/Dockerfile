FROM dsarchive/dsa_common:latest

WORKDIR /wsi_deid


RUN apt-get update
RUN apt install libdmtx-dev libdmtx0b
RUN pip install  girder-ldap pyyaml pylibdmtx
RUN pip install wsi-deid@git+https://github.com/digitalslidearchive/dsa-wsi-deid

# Copy the package first
RUN pip install git+https://github.com/dgutman/nci-dsa-deid
RUN mkdir -p /opt/girder/plugins
COPY plugins/oauth /opt/girder/plugins/oauth
RUN pip install -e /opt/girder/plugins/oauth
RUN girder build --dev