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
from components.collection_overview_panel import collection_overview_panel

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
        dbc.Tab(collection_overview_panel, label="Collection Items", tab_id="collection-items"),
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
    """
    Process a single file row to determine its metadata match status and deid workflow status.
    
    Returns:
        dict: Updated row with match_result, deidStatus, curDsaPath, and valid fields
    """
    validator = Draft7Validator(s.SCHEMA)
    
    # Initialize default values
    row["match_result"] = "NoMeta"
    row["curDsaPath"] = None
    row["InputFileName"] = row["name"]
    
    # Step 1: Handle metadata matching
    _process_metadata_matching(row, metadataDict, COLS_FOR_COPY)
    
    # Step 2: Handle sample ID generation
    _process_sample_id(row)
    
    # Step 3: Handle file type validation and output filename
    if not _process_file_type_and_output_name(row):
        # File type not supported - skip deid status processing
        pass
    else:
        # Step 4: Check deid workflow status
        _process_deid_workflow_status(row)
    
    # Step 5: Validate the complete row
    _validate_row(row, validator)
    
    return row


def _process_metadata_matching(row, metadataDict, COLS_FOR_COPY):
    """Handle metadata matching logic."""
    if row["name"] in metadataDict:
        row["match_result"] = "Match"
        matched_metadata = metadataDict[row["name"]]
        for col in COLS_FOR_COPY:
            if col in matched_metadata:
                row[col] = matched_metadata[col]
    else:
        # No metadata found - fill with empty values
        for col in COLS_FOR_COPY:
            row[col] = " "
        row["valid"] = False


def _process_sample_id(row):
    """Handle sample ID generation if missing."""
    if row.get("SampleID") == " ":
        today = datetime.date.today()
        row["SampleID"] = f"Batch-{today.strftime('%Y%m%d')}"


def _process_file_type_and_output_name(row):
    """Handle file type validation and output filename generation. Returns True if file is supported."""
    if not row["name"].endswith(".svs"):
        row["deidStatus"] = "FileType Not Supported"
        row["OutputFileName"] = " "
        return False
    
    # Generate output filename if not provided
    if not row.get("OutputFileName"):
        row["OutputFileName"] = os.path.splitext(row["name"])[0] + ".deid.svs"
    
    # Ensure proper .svs extension
    if not row["OutputFileName"].endswith(".svs"):
        if len(row["OutputFileName"].split(".")) > 1:
            row["OutputFileName"] = row["OutputFileName"] + ".svs"
    
    return True


def _process_deid_workflow_status(row):
    """Check and set deid workflow status based on existing files."""
    existing_file_path = checkForExistingFile(row["OutputFileName"])
    
    if existing_file_path:
        # File exists in workflow - determine status based on path
        row["curDsaPath"] = existing_file_path
        row["deidStatus"] = _determine_workflow_status(existing_file_path)
    else:
        # File not found in workflow
        row["deidStatus"] = "Ready for Processing"


def _determine_workflow_status(file_path):
    """Determine workflow status based on file path."""
    if file_path.startswith("/collection/WSI DeID/Approved"):
        return "In Approved Status"
    elif file_path.startswith("/collection/WSI DeID/Redacted"):
        return "In Redacted Folder"
    elif file_path.startswith("/collection/WSI DeID/AvailableToProcess"):
        return "AvailableToProcess Folder"
    elif "(" in file_path and ")" in file_path:
        return "DUPLICATE - Already in Workflow"
    else:
        return "Unknown Workflow Status"


def _validate_row(row, validator):
    """Validate the complete row and set valid status."""
    if validator.is_valid(row):
        row["valid"] = "ValidRow"
    else:
        row["valid"] = "INVALID"


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
