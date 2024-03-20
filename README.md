# NCI DSA Deid Tool
DSA companion web application for the DSA WSI Deid Plugin.

To run this application you will need to have Docker installed. This application was tested with Ubuntu 22.04.4 LTS. Instructions provided are for this system but should be applicable to other OS with minor modifications.

This application works in tandem with a running DSA instance. By default the DSA instance we are using can be reached [here](https://wsi-deid.pathology.emory.edu/#).

**How to run web application:**
1. Clone this repository.
2. Using the terminal navigate into the repository.
3. ```$ cd docs/app```
4. ```$ cp example.env .env```
5. Modify the newly created .env file and add your DSA API key.
6. ```$ docker build -t deid .```
    * You can choose to build the image with a different name, here we choose "deid".
7. ```$ docker run -it --rm -p8050:8050 -v .:/app deid```
    * The application by default will run in localhost:8050, though this can be configured.
