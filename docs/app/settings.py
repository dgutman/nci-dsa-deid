import json, girder_client

SCHEMA_FILE = "importManifestSchema.json"
TEST_MODE = True
TEST_FILENAME = "exampleData_112322.csv"
DSA_BASE_URL = "https://wsi-deid.pathology.emory.edu/api/v1"


## During debugging, I am going to get a default item list so I don't have to keep clicking
gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)

defaultItemList = list(gc.listItem("6477c00e309a9ffde6689635"))

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
    {"field": "name", "header": "fileName", "tooltipField": "name"},
    {"field": "size", "header": "File Size"},
    {"field": "match_result", "tooltipField": "match_result"},
    {"field": "OutputFileName", "tooltipField": "OutputFileName"},
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
