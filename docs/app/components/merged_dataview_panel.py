from dash import callback, State, Output, Input, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from os import getenv
from girder_client import GirderClient
import dash_ag_grid as dag
import settings as s

import utils.barcodeHelpers as bch
import utils.deidHelpers as hlprs
from utils.utils import submitImageForDeId, processDeIDset

checklist = html.Div(
    [
        dbc.Label("DeID Flags"),
        dbc.Checklist(
            options=[
                {
                    "label": "BruteForce AvailableToProcessFolder",
                    "value": "batchSubmit_atp",
                },
                {"label": "BruteForce Redacted", "value": "batchSubmit_redacted"},
            ],
            # value=[1],
            id="deid-flag-inputs",
        ),
    ]
)

merged_dataview_panel = html.Div(
    [
        html.Span(
            [
                dbc.Button(
                    "Submit for DeID",
                    id="submit-deid-button",
                    color="primary",
                    disabled=False,
                    n_clicks=0,
                ),
                dbc.Button(
                    "Check ",
                    id="validate-deid-status-button",
                    color="warning",
                    disabled=False,
                    style={"padding": "5px"},
                ),
                checklist,
            ],
            id="submit-deid-button-span",
            style={
                "display": "flex",
                "gap": "10px",
            },  # This adds equal space between all items in the span if you prefer this way
        ),
        html.Div(id="mergedImageSet"),
        dbc.Label(
            "Note: SampleID becomes the initial folder the app groups things by during DEID"
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(id="deid-status-output"), width=3),
                dbc.Col(
                    html.Img(
                        id="currentItemThumbnail", src="", style={"maxHeight": 256}
                    ),
                    width=3,
                ),
                dbc.Col(
                    [
                        html.Img(
                            id="currentItemMacro",
                            src="",
                            style={"maxHeight": 256},
                        ),
                    ],
                    width=3,
                ),
            ]
        ),
    ]
)


# Callbacks
@callback(
    [
        Output("submit-button-state-store", "data"),
        Output("submit-deid-button", "disabled"),
    ],
    [
        Input("submit-deid-button", "n_clicks"),
        State("submit-button-state-store", "data"),
    ],
    prevent_initial_call=True,
)
def disable_button(n_clicks, button_data):
    if n_clicks:
        button_data["disabled"] = True

        return button_data, True
    else:
        return button_data, False


@callback(Output("mergedImageSet", "children"), Input("mergedItem_store", "data"))
def updateMergedDatatable(mergeddata):
    if mergeddata:
        for row in mergeddata:
            if row.get("match_result", None) == "Match":
                row["match_result_style"] = {"backgroundColor": "orange"}
            elif row["match_result"] == "NoMeta":
                row["match_result_style"] = {"backgroundColor": "orange"}
            else:
                row["match_result_style"] = {}

            if row["valid"]:
                row["valid_style"] = {"backgroundColor": "green"}
            else:
                row["valid_style"] = {}

        merged_grid = [
            dag.AgGrid(
                rowData=mergeddata,
                id="merged-datagrid",
                columnDefs=s.MERGED_COL_DEFS,
                defaultColDef=dict(
                    resizable=True,
                    editable=True,
                    sortable=True,
                    maxWidth=250,
                    minWidth=30,
                    cellStyle={
                        "styleConditions": [
                            {
                                "condition": "params.value == 'NoMeta'",
                                "style": {"backgroundColor": "orange"},
                            },
                            {
                                "condition": "params.value == 'Match'",
                                "style": {
                                    "backgroundColor": "purple",
                                    "color": "white",
                                },
                            },
                            {
                                "condition": "params.colDef.headerName == 'Make'",
                                "style": {"backgroundColor": "red", "color": "yellow"},
                            },
                            {
                                "condition": "params.value == 'Submitted'",
                                "style": {"backgroundColor": "green", "color": "white"},
                            },
                        ]
                    },
                ),
                dashGridOptions={
                    "toolTipShowDelay": 0.2,
                    "rowSelection": "single",
                    "rowHeight": 20,
                },
            ),
        ]
        return merged_grid
    else:
        return [html.Div()]


@callback(
    [
        Output("mergedItem_store", "data", allow_duplicate=True),
        Output("submit-deid-button", "disabled", allow_duplicate=True),
    ],
    [
        Input("submit-deid-button", "n_clicks"),
        State("mergedItem_store", "data"),
        State("deid-flag-inputs", "value"),
        State("metadata_store", "data"),
        State("user-store", "data"),
    ],
    prevent_initial_call=True,
)
def submit_for_deid(n_clicks, data, deidFlags, metadataList, user_data):
    # Submit for de-identification.
    gc = GirderClient(apiUrl=getenv("DSA_API_URL"))
    gc.token = user_data["token"]

    if not n_clicks or not data:
        raise PreventUpdate

    ## Need to turn this into an array it it's null
    if not deidFlags:
        deidFlags = []

    for row in data:
        # print(row)
        curDsaPath = row.get("curDsaPath", None)
        # print(curDsaPath,row)
        if curDsaPath:
            if curDsaPath.startswith("/collection/WSI DeID/Approved"):
                row["deidStatus"] = "In Approved Status"

            elif curDsaPath.startswith("/collection/WSI DeID/Redacted"):
                row["deidStatus"] = "In Redacted Folder"

            elif curDsaPath.startswith("/collection/WSI DeID/AvailableToProcess"):
                row["deidStatus"] = "AvailableToProcess Folder"

        elif row.get("deidStatus", None) in ["FileType Not Supported"]:
            row["deidStatus"] = "SKIPPED"

        elif row.get("match_result") in ["Match", "NoMeta"]:
            submitImageForDeId(gc, row)
            row["deidStatus"] = "Submitted"
        else:
            row["deidStatus"] = "SKIPPED"

    processDeIDset(gc, data, deidFlags)

    # Re-enable the button after processing
    return data, False


@callback(Output("currentItemMacro", "src"), Input("merged-datagrid", "selectedRows"))
def displayMacroForSelectedRow(selected):
    if selected:
        thumbSrc = hlprs.get_thumbnail_as_b64(selected[0]["_id"])
        return thumbSrc


@callback(
    Output("currentItemThumbnail", "src"), Input("merged-datagrid", "selectedRows")
)
def displayThumbnailForSelectedRow(selected):
    if selected:
        # img = hlprs.create_image()
        selected = selected[0]  ## Only returns a single row, but it's an array
        ### Hack for now  so I copy over the metadata needed..
        selected["meta"]["deidUpload"] = selected
        outputFileName = selected["meta"]["deidUpload"].get(
            "OutputFileName", "WrongTag"
        )
        deidBarCode = hlprs.add_barcode_to_image(
            selected, outputFileName, item=selected
        )

        # h, w = deidBarCode.size
        encoded_image = hlprs.image_to_base64(deidBarCode)

        return f"data:image/png;base64,{encoded_image}"
