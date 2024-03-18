from dash import html
import pandas as pd
import jsonschema
from jsonschema import Draft7Validator
import settings as s
import io, base64, json, jsonschema, random, datetime
import dash_ag_grid as dag
import docs.app.config as config

"""This is a set of helper functions for debug purposes for the NCI DEID app
This includes some cleanup functions to remove images during testing that were uploaded 
but had parsing issues, as well as functions to test/apply the schema"""

schema = s.SCHEMA


def validate_df(df):
    """Validate DataFrame against schema and return DataFrame with 'valid' column and 'error' column."""
    df["valid"] = True
    df["error_cols"] = ""

    validator = Draft7Validator(schema)
    for i, row in df.iterrows():
        row_dict = row.to_dict()

        error_list = validator.iter_errors(row_dict)
        error_tree = jsonschema.exceptions.ErrorTree(validator.iter_errors(row_dict))

        invalid_cols = []
        for e in error_list:
            ##pass
            invalid_cols.append(*e.path)
        if invalid_cols:
            print(",".join(invalid_cols))
        df.at[i, "valid"] = False
        df.at[i, "error_cols"] = str(invalid_cols)

    return df


def read_file_from_system(filename, filetype):
    if "csv" in filetype:
        return pd.read_csv(filename)
    elif "xls" in filetype:
        return pd.read_excel(filename)
    else:
        raise ValueError("Unsupported file type.")


def read_file_from_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    if "csv" in filename:
        return pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    elif "xls" in filename:
        return pd.read_excel(io.BytesIO(decoded))
    else:
        raise ValueError("Unsupported file type.")


def parse_testfile(filename):
    """This will parse a file that is local and hardcoded for demo purposes"""
    try:
        # Extracting the file extension to determine the filetype
        filetype = filename.split(".")[-1]
        df = read_file_from_system(filename, filetype)
    except Exception as e:
        return html.Div(["There was an error processing this file."])

    # Validate the DataFrame
    df = validate_df(df)

    return html.Div(
        [
            html.H5(filename),
            html.H6(datetime.datetime.now()),
            dag.AgGrid(
                rowData=df.to_dict("records"),
                columnDefs=[{"headerName": i, "field": i} for i in df.columns],
                id="metadataTable",
            ),
        ]
    )


def parse_contents(contents, filename, date):
    # try
    df = read_file_from_contents(contents, filename)
    # except Exception as e:
    #     return html.Div(["There was an error processing this file."])

    # Validate the DataFrame
    df = validate_df(df)

    return (
        html.Div(
            [
                html.H5(filename),
                html.H6(datetime.datetime.fromtimestamp(date)),
                dag.AgGrid(
                    rowData=df.to_dict("records"),
                    columnDefs=[{"headerName": i, "field": i} for i in df.columns],
                    id="dag_metadataTable",
                ),
                html.Hr(),  # horizontal line
                html.Div("Raw Content"),
                html.Pre(
                    contents[0:200] + "...",
                    style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
                ),
            ],
        ),
        df.to_dict("records"),
    )


def print_all_errors(error_tree):
    for error in error_tree.errors:
        print(f"Error at {list(error.path)}: {error.message}")


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
        print(
            f'Deleted {results[0]} items and {results[1]} folders in folder {f["name"]}'
        )


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
        redactList["metadata"]["internal;openslide;aperio.Date"] = (
            generate_system_redaction_list_entry(
                "01/01/" + metadata["openslide"]["aperio.Date"][6:]
            )
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
        prefix
        + version
        + "\n"
        + "|".join(
            ["%s = %s" % (k, v) for k, v in sorted(get_deid_field_dict(item).items())]
        )
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
