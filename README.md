# nci-dsa-deid
DSA Plugin for image de-identification using the dsa-wsi-deid plugin

**DSA instance used.**
Link: [https://wsi-deid.pathology.emory.edu](https://wsi-deid.pathology.emory.edu/#)

**Requirements**
* Docker installed.

**Instructions**
1. Clone repository (terminal example: ```$ git clone https://github.com/dgutman/nci-dsa-deid.git```) 
2. Create environmental file by creating a ".env" file, copying the contents of "example.env" to it and modifying it appropriately.
* ```$ cp example.env .env``` and add you DSA token for user access
* ```$ cd docs/app```
* Build the image: ```$ docker build -t <name of choice> .```
    - If running on Mac, add "--platform linux/amd64" to build it appropriately
* Run it: ```$ docker run -it --rm -p8050:8050 --v .:/app <name of choice>```
* The app should run in localhost:8050