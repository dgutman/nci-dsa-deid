import json
from girder_client import GirderClient
import logging

import os
from os import getenv

DEBUG = getenv("DEBUG", False)

SCHEMA_FILE = "importManifestSchema.json"
TEST_MODE = False
TEST_FILENAME = "exampleData_112322.csv"

DSAKEY = os.getenv("DSAKEY")
DSA_BASE_URL = os.getenv("DSA_API_URL")


# try:
#     # Authenticate the client.
#     gc.authenticate(apiKey=DSAKEY)
#     DSA_LOGIN_SUCCESS = True

#     # Look for the unfiled folder id, if not there then create it.
#     try:
#         response = gc.get("resource/lookup?path=/collection/WSI DeID/Unfiled")
#     except:
#         response = None

#     if response:
#         DSA_UNFILED_FOLDER = response["_id"]
#     else:
#         # Look for collection.
#         try:
#             response = gc.get("resource/lookup?path=/collection/WSI DeID")
#         except:
#             # This breaks the app, by default your server should have this collection.
#             raise Exception("WSI DeID collection not found, app cannot run this way.")

#         try:
#             DSA_UNFILED_FOLDER = gc.createFolder(
#                 response["_id"], "Unfiled", parentType="collection"
#             )["_id"]
#         except:
#             DSA_UNFILED_FOLDER = None
# except:
#     DSA_LOGIN_SUCCESS = False

#     # Look for unfiled folder, if it does not exist then remove.
#     try:
#         response = gc.get("resource/lookup?path=/collection/WSI DeID/Unfiled")
#         DSA_UNFILED_FOLDER = response["_id"]
#     except:
#         DSA_UNFILED_FOLDER = None

# if TEST_MODE:
#     # For debug mode get a list of item to load to the table on startup.
#     # TEST_FOLDERID = "64da4e64309a9ffde668b9e6"  ## VISUM FOLDER
#     # TEST_FOLDERID = "6452a8b1239ec54642356cad"  ## This has 31 files
#     TEST_FOLDERID = "jc was here"  # for testing, this should crash the application if the failsafe is not set up well
#     defaultItemList = list(gc.listItem(TEST_FOLDERID))

# Set up logging.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a file handler
log_filename = "app.log"
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)

### These are fields that should be copied from the metadata file to the merged file
COLS_FOR_COPY = [
    "SampleID",
    "REPOSITORY",
    "STUDY",
    "PROJECT",
    "CASE",
    "BLOCK",
    "ASSAY",
    "INDEX",
    "ImageID",
    "OutputFileName",
]

MERGED_COL_DEFS = [
    {
        "field": "match_result",
        "tooltipField": "match_result",
        "headerName": "Match Result",
        "width": 150,
        "editable": False,
    },
    {
        "field": "deidStatus",
        "width": 150,
        "editable": False,
        "cellStyle": {
            "styleConditions": [
                {
                    "condition": 'params.value == "AvailableToProcess Folder"',
                    "style": {"backgroundColor": "#FFFD73"},
                },
                {
                    "condition": 'params.value == "In Redacted Folder"',
                    "style": {"backgroundColor": "#FFE073"},
                },
                {
                    "condition": 'params.value == "In Approved Status"',
                    "style": {"backgroundColor": "#9DFF73"},
                },
                {
                    "condition": 'params.value == "In Original Folder"',
                    "style": {"backgroundColor": "#0CFE00"},
                },
            ]
        },
    },
    {"field": "name", "header": "fileName", "tooltipField": "name", "editable": False},
    {
        "field": "OutputFileName",
        "tooltipField": "OutputFileName",
        "width": 300,
        "editable": False,
    },
    {
        "field": "curDsaPath",
        "tooltipField": "curDsaPath",
        "width": 450,
        "editable": False,
    },
    {"field": "size", "header": "File Size", "width": 160, "editable": False},
    {"field": "SampleID"},
    {"field": "REPOSITORY"},
    {"field": "STUDY"},
    {"field": "PROJECT"},
    {"field": "CASE"},
    {"field": "BLOCK"},
    {"field": "ASSAY"},
    {"field": "INDEX"},
    {"field": "ImageID"},
    {"field": "valid"},
]

with open(SCHEMA_FILE) as file:
    SCHEMA = json.load(file)
