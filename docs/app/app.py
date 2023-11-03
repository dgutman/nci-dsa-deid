# Library imports
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import Dash, State, callback, callback_context, dcc, ctx
from jsonschema import Draft7Validator

from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform, html
from components.merged_dataview_panel import merged_data_panel, checkForExistingFile
import os
from concurrent.futures import ThreadPoolExecutor

# Local modules
from deidHelpers import parse_testfile, validate_df, parse_contents
from components.dsaFileBrowser import slideListTab_content

from components.dsa_login_panel import dsa_login_panel
import settings as s
import dash_mantine_components as dmc
from components.instructionPanel import instructions_tab
from components.metaDataUpload_panel import metadata_upload_layout
import json


external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
]


app = DashProxy(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
    transforms=[MultiplexerTransform()],
)


tabs = dbc.Tabs(
    [
        dbc.Tab(
            slideListTab_content, label="Slides For DeID", tab_id="slides-for-deid"
        ),
        dbc.Tab(metadata_upload_layout, label="Slide Metadata ", tab_id="metadata"),
        # dbc.Tab(debug_buttons, label="Debug Tools", tab_id="debug-tools"),
        dbc.Tab(merged_data_panel, label="Merged Data", tab_id="merged-data"),
        dbc.Tab(instructions_tab, label="Instructions", tab_id="intructions-tab"),
    ],
    id="main-tabs",
)


## TO DO .. MAKE THIS ASYNCHRONOUS WITH CALLBACK AT ON THE SCREEN THAT ALSO DISALES THE SUBMIT BUTTON!!


app.layout = dmc.NotificationsProvider(
    html.Div(
        [
            html.Script(src="/assets/customRenderer.js"),
            html.Div(
                id={"type": "selected-folder", "id": "TBD", "level": 0},
                style={
                    "font-size": "20px",
                    "font-weight": "bold",
                    "margin-bottom": "20px",
                },
            ),
            # modal_tree,
            dsa_login_panel,
            dcc.Store(id="itemList_store", data=s.defaultItemList),
            dcc.Store(id="metadata_store"),
            dcc.Store(id="mergedItem_store"),
            html.Div(id="notifications-container"),
            dcc.Store({"type": "datastore", "id": "ils", "level": 2}),
            html.Div(id="last-clicked-folder", style={"display": "none"}),
            tabs,
        ]
    )
)


## This can be praallelized
def process_row(row, COLS_FOR_COPY):
    row["match_result"] = "NoMeta"
    row["curDsaPath"] = None
    for idx, col in enumerate(COLS_FOR_COPY):
        row[col] = str(idx)
    row["valid"] = True
    row["OutputFileName"] = os.path.splitext(row["name"])[0] + ".deid.svs"

    deidFileStatus = checkForExistingFile(row["OutputFileName"])
    row["curDsaPath"] = deidFileStatus

    return row


@app.callback(
    [
        Output("mergedItem_store", "data"),
        Output("main-tabs", "active_tab"),  # Add this line
    ],
    Input("check-match-button", "n_clicks"),
    Input("no-meta-deid-button", "n_clicks"),
    State("metadata_store", "data"),
    State("itemList_store", "data"),
    Input("validate-deid-status-button", "n_clicks"),
    prevent_initial_call=True,
)
def check_name_matches(
    checkmatch_clicks, nometa_button, metadata, itemlist_data, updateItemStatus
):
    ## Should be based on the context... need to debug
    ## Really need to get the context here in the future??

    if nometa_button or updateItemStatus:
        print("Updating item status..")
        with ThreadPoolExecutor() as executor:
            results = list(
                executor.map(
                    process_row, itemlist_data, [s.COLS_FOR_COPY] * len(itemlist_data)
                )
            )

        return results, "merged-data"

    # Create a mapping from filename to its metadata
    ### Make sure I only run this is there is actually metadata..
    if metadata:
        metadata_mapping = {row["InputFileName"]: row for row in metadata}

        s.logger.info(f"{len(metadata)} rows are in the metadata table")
        s.logger.info(f"{len(itemlist_data)} rows are in the current itemlist")

        try:
            for row in itemlist_data:
                if row["name"] in metadata_mapping:
                    row["match_result"] = "Match"
                    matched_metadata = metadata_mapping[row["name"]]
                    for col in s.COLS_FOR_COPY:
                        if (
                            col in matched_metadata
                        ):  # Ensure the column exists in the metadata
                            row[col] = matched_metadata[col]
                else:
                    row["match_result"] = "No Match"
                row["valid"] = True

            return itemlist_data, "merged-data"
        except Exception as e:
            print("Something broke:", e)
            return None, "slides-for-deid"
    return None, "slides-for-deid"


## Changing this to deal with only a single input..
@callback(
    Output("output-data-upload", "children"),
    Output("metadata_store", "data", allow_duplicate=True),
    Input("load-test-data-button", "n_clicks"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
    prevent_initial_call=True,
)
def update_output(testdata_n_clicks, file_content, file_name, file_upload_date):
    if testdata_n_clicks or s.TEST_MODE:
        # print("test data loader pushed")
        return parse_testfile(s.TEST_FILENAME)

    ### TO DO:  Handle exceptoin better, may want to use the mantine_notification provider
    valid_extensions = ("csv", "xlsx")
    if file_name.endswith(valid_extensions):
        print("Valid extension found")
    else:
        print("Invalid exception found")
        return [html.Div()], {}
    ### Check and see if the file_name ends with .csv or .xlsx

    if file_content is not None:
        uploaded_file_layout, uploaded_file_data = parse_contents(
            file_content, file_name, file_upload_date
        )

        return [uploaded_file_layout], uploaded_file_data

    return [html.Div()], {}


if __name__ == "__main__":
    ## Clear the log between restarts
    with open(s.log_filename, "w"):
        pass
    app.run(debug=True, host="0.0.0.0")
