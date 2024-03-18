from dash import html
import pandas as pd

import jsonschema
from jsonschema import Draft7Validator
import settings as s

import io, base64, json, jsonschema, random, datetime
import dash_ag_grid as dag
import config
import base64

# """This is a set of helper functions for debug purposes for the NCI DEID app
# This includes some cleanup functions to remove images during testing that were uploaded
# but had parsing issues, as well as functions to test/apply the schema"""

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
        # print(error_tree)
        invalid_cols = []
        for e in error_list:
            ##pass
            invalid_cols.append(*e.path)
            print(invalid_cols)
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
        return pd.read_csv(io.StringIO(decoded.decode("utf-8")), on_bad_lines="skip")
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
        # print("data frame was read", filename)
    except Exception as e:
        return html.Div(["There was an error processing this file."])

    return df


def parse_contents(contents, filename, date):
    ## If the file is not being uploaded manually, I need to inject a valid time stamp
    if not date:
        date = datetime.datetime.now().timestamp()

    if contents == "TEST_FILE":
        df = parse_testfile(filename)
    elif contents is not None:
        df = read_file_from_contents(contents, filename)

    # Validate the DataFrame
    if df is not None:

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


# def print_all_errors(error_tree):
#     for error in error_tree.errors:
#         print(f"Error at {list(error.path)}: {error.message}")


# wsiDeidFolderPathsForCleanup = [
#     "/WSI DeID/Unfiled",
#     "/WSI DeID/Redacted",
#     "/WSI DeID/Reports/Import Job Reports",
#     "/WSI DeID/Redacted",
#     "/WSI DeID/Approved",
# ]


# def cleanupFoldersByPath(gc, folderPathList):
#     """This converts a list of paths that are the relative girder path
#     and converts them into actual girder folder objects.. i.e. gives me the _id field
#     I need to access them.  This should also make it easier ti switch between systems
#     since I don't have to hard code _ids which frequently change"""
#     for fpl in folderPathList:
#         f = gc.get(f"resource/lookup?path=/collection{fpl}")
#         results = cleanupFolder(gc, f["_id"])
#         print(
#             f'Deleted {results[0]} items and {results[1]} folders in folder {f["name"]}'
#         )

#     return html.Div(
#         [
#             html.H5(filename),
#             html.H6(datetime.datetime.now()),
#             dag.AgGrid(
#                 rowData=df.to_dict("records"),
#                 columnDefs=[{"headerName": i, "field": i} for i in df.columns],
#                 id="metadataTable",
#             ),
#         ]
#     )

# def cleanupFolder(gc, folderId):
#     """This will remove all items and folders from a given input folderID"""
#     ### Get all thei the items in the current Folder and remove them
#     itemsDeleted = 0
#     for i in gc.listItem(folderId):
#         gc.delete(f'item/{i["_id"]}')
#         itemsDeleted += 1

#     foldersDeleted = 0
#     for f in gc.listFolder(folderId):
#         gc.delete(f'folder/{f["_id"]}')
#         foldersDeleted += 1

#     return itemsDeleted, foldersDeleted
