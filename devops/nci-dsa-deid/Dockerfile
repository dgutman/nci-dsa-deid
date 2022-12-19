FROM dsarchive/dsa_common:latest

RUN pip install wsi-deid@git+https://github.com/digitalslidearchive/dsa-wsi-deid
RUN apt-get update
RUN apt-get install libdmtx-dev -y 
RUN pip install pylibdmtx
