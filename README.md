# NCI DSA Deid Tool
DSA companion web application for the DSA WSI Deid Plugin.

To run this application you will need to have Docker and git installed. This application was tested with Ubuntu 22.04.4 LTS. Instructions provided are for this system but should be applicable to other OS with minor modifications.

This application works in tandem with a running DSA instance. The DSA instance used is specified in the .env file (see instructions).

**Instructions**
1. Clone this repository: ```$ git clone https://github.com/dgutman/nci-dsa-deid.git```
2. Using the terminal navigate into the repository: ```$ cd nci-dsa-deid```
3. Create .env file by copying the example file: ```$ cp example.env .env```
4. Modify the newly created .env filling in the value for the DSA instance API URL and user API token.
    * For questions on this step, email David Gutman.
6. Run the application: ```$ docker run -it --rm --env-file ./.env -p8050:8050 jvizcar/nci-deid:latest```
    * The application by default will run on localhost:8050, though this can be configured.
    * The application has an instruction panel for instructions on how to use it.
