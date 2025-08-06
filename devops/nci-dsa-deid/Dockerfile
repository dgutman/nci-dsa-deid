FROM dsarchive/dsa_common:latest

WORKDIR /wsi_deid


RUN apt-get update && \
    apt-get install -y libdmtx-dev libdmtx0b && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir girder-ldap pyyaml pylibdmtx && \
    pip install --no-cache-dir wsi-deid@git+https://github.com/digitalslidearchive/dsa-wsi-deid && \
    pip install --no-cache-dir git+https://github.com/dgutman/nci-dsa-deid && \
    rm -rf /root/.cache/pip

# Copy the package first
RUN mkdir -p /opt/girder/plugins
COPY plugins/oauth /opt/girder/plugins/oauth
RUN pip install --no-cache-dir -e /opt/girder/plugins/oauth && rm -rf /root/.cache/pip
RUN girder build --dev