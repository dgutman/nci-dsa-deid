# Library imports
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from jsonschema import Draft7Validator
import datetime
from dash_iconify import DashIconify
from concurrent.futures import ThreadPoolExecutor
import settings as s
from dash import Dash, State, callback, dcc, Input, Output, State, html, no_update

import os
from os import getenv

from components.dsaFileBrowser import slideListTab_content
from components.dsa_login_panel import dsa_login_panel
from components.instructionPanel import instructions_tab
from components.metaDataUpload_panel import metadata_upload_layout
from components.merged_dataview_panel import merged_data_panel, checkForExistingFile

# Get prefix from environment variable, defaulting to '/' if not set
requests_prefix = getenv('REQUESTS_PREFIX', '/')

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
   
]

app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    url_base_pathname=requests_prefix,
    serve_locally=True
)

tabs = dbc.Tabs(
    [
        dbc.Tab(
            slideListTab_content, label="Slides For DeID", tab_id="slides-for-deid"
        ),
        dbc.Tab(metadata_upload_layout, label="Slide Metadata ", tab_id="metadata"),
        dbc.Tab(merged_data_panel, label="Merged Data", tab_id="merged-data"),
        dbc.Tab(instructions_tab, label="Instructions", tab_id="intructions-tab"),
    ],
    id="main-tabs",
)

app.layout = dmc.NotificationsProvider(
    html.Div(
        [
            html.Script(src="/assets/customRenderer.js"),
            dsa_login_panel,
            dcc.Store(id="itemList_store", data=[]),
            dcc.Store(id="metadata_store"),
            dcc.Store(id="mergedItem_store"),
            html.Div(id="notifications-container"),
            dcc.Store({"type": "datastore", "id": "ils", "level": 2}),
            html.Div(id="last-clicked-folder", style={"display": "none"}),
            tabs,
        ]
    )
)


## This can be parallelized
def process_row(row, COLS_FOR_COPY, metadataDict):
    validator = Draft7Validator(s.SCHEMA)
    row["match_result"] = "NoMeta"
    row["curDsaPath"] = None

    row["InputFileName"] = row[
        "name"
    ]  ## the name of the file is the input file name per the schema

    if row["name"] in metadataDict:

        row["match_result"] = "Match"
        matched_metadata = metadataDict[row["name"]]
        for col in COLS_FOR_COPY:
            if col in matched_metadata:
                row[col] = matched_metadata[col]
    else:
        ### Just insert null values for the required metadata columns..
        for idx, col in enumerate(COLS_FOR_COPY):
            row[col] = " "  # str(idx)
        row["valid"] = False

    ## Change the default to a datetime instead of just 0
    today = datetime.date.today()

    if (
        row["SampleID"] == " "
    ):  ## If the sampleID is empty, then we will generate a new one
        row["SampleID"] = "Batch-%s" % today.strftime("%Y%m%d")

    if not row["name"].endswith(".svs"):
        row["deidStatus"] = "FileType Not Supported"
        row["OutputFileName"] = " "

    else:
        if not row["OutputFileName"]:
            ## In this case, the filename was not provided and so we will just generate one
            row["OutputFileName"] = os.path.splitext(row["name"])[0] + ".deid.svs"

        ## Check for case where file extension is not added to the outputfilene
        if not row["OutputFileName"].endswith(
            ".svs"
        ):  ### Check for proper extension when I add support for other file types..
            if len(row["OutputFileName"].split(".")) > 1:  ## Work around null filknames
                row["OutputFileName"] = row["OutputFileName"] + ".svs"

        deidFileStatus = checkForExistingFile(row["OutputFileName"])

        if deidFileStatus:
            if deidFileStatus.startswith("/collection/WSI DeID/Approved"):
                row["deidStatus"] = "In Approved Status"

            elif deidFileStatus.startswith("/collection/WSI DeID/Redacted"):
                row["deidStatus"] = "In Redacted Folder"

            elif deidFileStatus.startswith("/collection/WSI DeID/AvailableToProcess"):
                row["deidStatus"] = "AvailableToProcess Folder"

            if "deidStatus" in row:
                row["curDsaPath"] = deidFileStatus

    if validator.is_valid(row):
        row["valid"] = "ValidRow"
    else:
        row["valid"] = "INVALID"

    return row


@callback(
    [
        Output("mergedItem_store", "data"),
        Output("main-tabs", "active_tab"),  # Add this line
        Output("notifications-container", "children", allow_duplicate=True),
    ],
    Input("check-match-button", "n_clicks"),
    Input("validate-deid-status-button", "n_clicks"),
    State("metadata_store", "data"),
    State("itemList_store", "data"),
    prevent_initial_call=True,
)
def check_name_matches(
    checkmatch_clicks,
    updateItemStatus,
    metadata,
    itemlist_data,
):
    if itemlist_data is None or not len(itemlist_data):
        return (
            no_update,
            no_update,
            dmc.Notification(
                title="Warning",
                action="show",
                id="simple-notify",
                message="Please choose a folder with images.",
                icon=DashIconify(icon="ic:round-celebration"),
            ),
        )
    elif metadata is None or not len(metadata):
        return (
            no_update,
            no_update,
            dmc.Notification(
                title="Warning",
                action="show",
                id="simple-notify",
                message="Please upload a metadata file.",
                icon=DashIconify(icon="ic:round-celebration"),
            ),
        )

    s.logger.info(f"{len(metadata)} rows are in the metadata table")
    s.logger.info(f"{len(itemlist_data)} rows are in the current itemlist")

    if metadata:
        metadata_mapping = {row["InputFileName"]: row for row in metadata}
    else:
        metadata_mapping = {}

    with ThreadPoolExecutor() as executor:
        results = list(
            executor.map(
                process_row,
                itemlist_data,
                [s.COLS_FOR_COPY] * len(itemlist_data),
                [metadata_mapping]
                * len(itemlist_data),  ## Note this oddity of science..
            )
        )

    return results, "merged-data", no_update


if __name__ == "__main__":
    ## Clear the log between restarts
    with open(s.log_filename, "w"):
        pass

    app.run_server(debug=True, host="0.0.0.0", threaded=True)
