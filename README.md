# NCI DSA Deid Tool
DSA companion web application for the DSA WSI Deid Plugin.

To run this application you will need to have Docker and git installed. This application was tested with Ubuntu 22.04.4 LTS. Instructions provided are for this system but should be applicable to other OS with minor modifications.

This application works in tandem with a running DSA instance. The DSA instance used is specified in the .env file (see instructions).

**Run Application through Docker**
1. Clone this repository: ```$ git clone https://github.com/dgutman/nci-dsa-deid.git```
2. Using the terminal navigate into the repository: ```$ cd nci-dsa-deid```
3. Create .env file by copying the example file: ```$ cp example.env .env```
4. Modify the newly created .env filling in the value for the DSA instance API URL and user API token.
    * For questions on this step, email David Gutman.
5. Run the application: ```$ docker run -it --rm --env-file ./.env -p8050:8050 jvizcar/nci-deid:latest```
    * Must be run in the root of the repository.
    * The application by default will run on localhost:8050, though this can be configured.
    * The application has an instruction panel for instructions on how to use it.

**Run Application for Developing by Mounting Local App Files**
1. Modify the last line of docs/app/app.py so debug=True.
2. After step 4 from above, run using this command: ```$ docker run -it --rm -env-file ./.env -p8050:8050 -v $(pwd)/docs/app:/app jvizcar/nci-deid:latest```
    * Note that you must run this at the root of the repository.
    * When running this way, you can modify the version "docs/app" locally and the app will restart to include the changes.

**Create a custom image with your modified version docs/app**
1. Use this command: ```$ docker build -t <name of choice> .```
    * Must be run in the root of repository.