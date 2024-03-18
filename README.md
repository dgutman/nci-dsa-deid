# nci-dsa-deid
DSA Plugin for image de-identification using the dsa-wsi-deid plugin

**DSA instance used.**
Link: [https://wsi-deid.pathology.emory.edu](https://wsi-deid.pathology.emory.edu/#)

**Instructions**
* Run using docker.
* clone this repository and navicate to it
* ```$ cp example.env .env``` and add you DSA token for user access
* ```$ cd docs/app```
* Build the image: ```$ docker build -t <name of choice> .```
    - If running on Mac, add "--platform linux/amd64" to build it appropriately
* Run it: ```$ docker run -it --rm -p8050:8050 --v .:/app <name of choice>```
* The app should run in localhost:8050