import json, girder_client, os
import logging
from dotenv import load_dotenv

SCHEMA_FILE = "importManifestSchema.json"
TEST_MODE = False
TEST_FILENAME = "exampleData_112322.csv"
DSA_BASE_URL = "https://wsi-deid.pathology.emory.edu/api/v1"
# TEST_FOLDERID = "6477c00e309a9ffde6689635"

TEST_FOLDERID = "64da4e64309a9ffde668b9e6"  ## VISUM FOLDER

DSA_UNFILED_FOLDER = (
    "/WSI DeID/Unfiled"  ## This is for internal bookkeeping, Will be hidden
)

DSA_LOGIN_SUCCESS = False

## During debugging, I am going to get a default item list so I don't have to keep clicking
gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)

defaultItemList = list(gc.listItem(TEST_FOLDERID))

load_dotenv(".env", override=True)
DSAKEY = os.getenv("DSAKEY")
# DSAKEY = None

if DSAKEY:
    gc.authenticate(apiKey=DSAKEY)
    DSA_LOGIN_SUCCESS = True
    print("App has logged into the DSA")


# Set up logging
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
    },
    {"field": "deidStatus", "width": 150},
    {"field": "name", "header": "fileName", "tooltipField": "name"},
    {"field": "OutputFileName", "tooltipField": "OutputFileName", "width": 300},
    {"field": "curDsaPath", "tooltipField": "curDsaPath", "width": 450},
    {"field": "size", "header": "File Size", "width": 160},
    {"field": "SampleID"},
    {"field": "REPOSITORY"},
    {"field": "STUDY"},
    {"field": "PROJECT"},
    {"field": "CASE"},
    {"field": "BLOCK"},
    {"field": "ASSAY"},
    {"field": "INDEX"},
    {"field": "ImageID"},
]


with open(SCHEMA_FILE) as file:
    SCHEMA = json.load(file)
