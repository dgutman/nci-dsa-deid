import json
import jsonschema
import random


"""This is a set of helper functions for debug purposes for the NCI DEID app
This includes some cleanup functions to remove images during testing that were uploaded 
but had parsing issues, as well as functions to test/apply the schema"""

wsiDeidFolderPathsForCleanup = [
    "/WSI DeID/Unfiled",
    "/WSI DeID/Redacted",
    "/WSI DeID/Reports/Import Job Reports",
    "/WSI DeID/Redacted",
    "/WSI DeID/Approved",
]


def cleanupFoldersByPath(gc, folderPathList):
    """This converts a list of paths that are the relative girder path
    and converts them into actual girder folder objects.. i.e. gives me the _id field
    I need to access them.  This should also make it easier ti switch between systems
    since I don't have to hard code _ids which frequently change"""
    for fpl in folderPathList:
        f = gc.get(f"resource/lookup?path=/collection{fpl}")
        results = cleanupFolder(gc, f["_id"])
        print(f'Deleted {results[0]} items and {results[1]} folders in folder {f["name"]}')


def cleanupFolder(gc, folderId):
    """This will remove all items and folders from a given input folderID"""
    ### Get all thei the items in the current Folder and remove them
    itemsDeleted = 0
    for i in gc.listItem(folderId):
        gc.delete(f'item/{i["_id"]}')
        itemsDeleted += 1

    foldersDeleted = 0
    for f in gc.listFolder(folderId):
        gc.delete(f'folder/{f["_id"]}')
        foldersDeleted += 1

    return itemsDeleted, foldersDeleted


def getSchemaValidator():
    """
    Return a jsonschema validator.

    :returns: a validator.
    """
    return jsonschema.Draft6Validator()


# def validateDataRow(validator, row, rowNumber, df):
#     """
#     Validate a row from a dataframe with a jsonschema validator.

#     :param validator: a jsonschema validator.
#     :param row: a dictionary of row information from the dataframe excluding
#         the Index.
#     :param rowNumber: the 1-based row number within the file for error
#         reporting.
#     :param df: the pandas dataframe.  Used to determine column number.
#     :returns: None for no errors, otherwise a list of error messages.
#     """
#     # folderNameField = config.getConfig("folder_name_field", "TokenID")
#     # imageNameField = config.getConfig("image_name_field", "ImageID")
#     # validateImageIDField = config.getConfig("validate_image_id_field", True)
#     if validator.is_valid(row):
#         return
#     errors = []
#     for error in validator.iter_errors(row):
#         try:
#             columnName = error.path[0]
#             columnNumber = df.columns.get_loc(columnName)
#             cellName = openpyxl.utils.cell.get_column_letter(columnNumber + 1) + str(
#                 rowNumber
#             )
#             errorMsg = f"Invalid {columnName} in {cellName}"
#         except Exception:
#             errorMsg = f"Invalid row {rowNumber} ({error.message})"
#             columnNumber = None
#         errors.append(errorMsg)
#     if validateImageIDField and row[imageNameField] != "%s_%s_%s" % (
#         row[folderNameField],
#         row["Proc_Seq"],
#         row["Slide_ID"],
#     ):
#         errors.append(
#             f"Invalid ImageID in row {rowNumber}; not composed of TokenID, Proc_Seq, and Slide_ID"
#         )
#     return errors


def get_standard_redactions_format_aperio(item, tileSource, tiffinfo, title):
    metadata = tileSource.getInternalMetadata() or {}
    title_redaction_list_entry = generate_system_redaction_list_entry(title)
    redactList = {
        "images": {},
        "metadata": {
            "internal;openslide;aperio.Filename": title_redaction_list_entry,
            "internal;openslide;aperio.Title": title_redaction_list_entry,
            "internal;openslide;tiff.Software": generate_system_redaction_list_entry(
                get_deid_field(item, metadata.get("openslide", {}).get("tiff.Software"))
            ),
        },
    }
    if metadata["openslide"].get("aperio.Date"):
        redactList["metadata"]["internal;openslide;aperio.Date"] = generate_system_redaction_list_entry(
            "01/01/" + metadata["openslide"]["aperio.Date"][6:]
        )
    return redactList


def get_deid_field(item, prefix=None):
    """
    Return a text field with the DeID Upload metadata formatted for storage.

    :param item: the item with data.
    :returns: the text field.
    """
    from . import __version__

    version = "DSA Redaction %s" % __version__
    if prefix and prefix.strip():
        if "DSA Redaction" in prefix:
            prefix.split("DSA Redaction")[0].strip()
        if prefix:
            prefix = prefix.strip() + "\n"
    else:
        prefix = ""
    return (
        prefix + version + "\n" + "|".join(["%s = %s" % (k, v) for k, v in sorted(get_deid_field_dict(item).items())])
    )


def get_deid_field_dict(item):
    """
    Return a dictionary with custom fields from the DeID Upload metadata.

    :param item: the item with data.
    :returns: a dictionary of key-vlaue pairs.
    """
    deid = item.get("meta", {}).get("deidUpload", {})
    if not isinstance(deid, dict):
        deid = {}
    result = {}
    limit = config.getConfig("upload_metadata_add_to_images")
    limit = set(limit if isinstance(limit, (list, set)) else [limit])
    for k, v in deid.items():
        if None not in limit and k not in limit:
            continue
        result["CustomField.%s" % k] = str(v).replace("|", " ")
    return result


def generate_system_redaction_list_entry(newValue):
    """Create an entry for the redaction list for a redaction performed by the system."""
    return {
        "value": newValue,
        "reason": "System Redacted",
    }


syntheticData = {
    "PatientID": ["Patient1", "Patient2", "Case12", "Patient3"],
    "SampleID": ["One", "Two", "Three"],
    "REPOSITORY": ["RepoA", "RepoB", "RepoC"],
    "STUDY": ["ABC", "DEF", "GH"],
    "PROJECT": ["Mando", "Lorian"],
    "CASE": ["CaseOne", "Case2", "Case3"],
    "BLOCK": [1, 2, 3, 4, 5],
    "INDEX": [1, 2, 3, 4, 5, 6],
}


def generate_random_data(data):
    random_data = {}
    for key in data.keys():
        random_data[key] = random.choice(data[key])
    return random_data


# random_data = generate_random_data(syntheticData)
# print(random_data)
