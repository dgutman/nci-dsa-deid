from dash import callback, State, dcc
from dash_extensions.enrich import Output, Input, html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

import io, base64, dash, json, girder_client
from pprint import pprint
import dash_ag_grid as dag
from settings import gc
from concurrent.futures import ThreadPoolExecutor
import json
import settings as s
import utils.barcodeHelpers as bch
import utils.deidHelpersV2 as hlprs

# import barcodeHelpers as bch
# import deidHelpersV2 as hlprs

## Trying to add diskcache functionality


def checkForExistingFile(deidOutputFileName):
    ### By design, an image following de-identification can not duplicate an existing file name
    ## or it would be extremely difficult to figure out which version is which.. this looks for the
    ## filename on the DSA and returns a path to where the file is located
    ## Dependinog on the path, we can then trigger other options..

    searchStatus = lookupDSAresource(deidOutputFileName)

    if searchStatus:
        try:
            itemId = searchStatus["item"][0]["_id"]

            resourcePath = gc.get(f"resource/{itemId}/path?type=item")
            if resourcePath:
                return resourcePath
        except:
            pass

    return None


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


merged_data_panel = html.Div(
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
        dcc.Store(id="submit-button-state-store", data={"disabled": False}),
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


@callback(
    Output("submit-button-state-store", "data"),
    Output("submit-deid-button", "disabled"),
    Input("submit-deid-button", "n_clicks"),
    State("submit-button-state-store", "data"),
    prevent_initial_call=True,
)
def disable_button(n_clicks, button_data):
    button_data["disabled"] = True
    return button_data, True


def lookupDSAresource(textPrefix, types=["item"], mode="prefix", limit=1):
    """This will use the girder_client to look for filenames in the DSA.  The app does not
    currently allow duplicate files to be created during the deID process.. this would make it extremely confusing
    to figure out what has and has not been deidentified"""
    searchOutput = gc.get(
        f'resource/search?q={textPrefix}&mode={mode}&limit={limit}&types=["item"]'
    )
    return searchOutput


## This is the folder things get filed into when they are unfiled/available to process..
unfiledFolder = gc.get(f"resource/lookup?path=/collection{s.DSA_UNFILED_FOLDER}")


def processImageSet(rows):
    """Note Rows vs row... this will process an entire set of rows, and move multiple images"""


## TO DO.. ADD MORE LOGIC HERE
def submitImageForDeId(row):
    # Your logic for submitting the image for DeID goes here
    ## So check if file is already un the unfiled Directory.. if so just use that..
    print("Processing", row)
    try:
        unfiledItemList = list(gc.listItem(unfiledFolder["_id"]))
    except:
        print("The call to unfiledItemList is hanging our failing.. not sure why")
    originalItemId_to_unfiledItemId = {}
    # print("unfilfedItemList", unfiledItemList)
    ##Sometimes files are already in the unfiled Folder, so I am looking up the references here
    ## Looking up by copyOfItem Id.. TBD is this is the best logic..
    for x in unfiledItemList:
        originalItemId_to_unfiledItemId[x.get("copyOfItem", None)] = x

    if row["_id"] not in originalItemId_to_unfiledItemId:
        itemCopyToUnfiled = gc.post(
            f'item/{row["_id"]}/copy?folderId={unfiledFolder["_id"]}'
        )
    else:
        itemCopyToUnfiled = originalItemId_to_unfiledItemId[row["_id"]]

    imageMeta = row

    gc.addMetadataToItem(itemCopyToUnfiled["_id"], {"deidUpload": row})

    newImageName = row["OutputFileName"]
    newImagePath = f'WSI DeID/AvailableToProcess/{row["SampleID"]}/{newImageName}'

    if newImageName.endswith(".svs"):
        print("Updating new image path which is:", newImageName)
        newImageName = newImageName.replace(
            ".svs", ""
        )  ## Need to clarify with D Manthey where/how to avoid adding the extension twice
    print("And nw should be", newImageName)

    try:
        fileUrl = f"resource/lookup?path=/collection/{newImagePath}.svs"  ## DEID adds extension during move
        fileExists = gc.get(fileUrl)
        fileExists = True
    except:
        fileExists = False
    ### See if the resource already exists  ..

    if not fileExists:
        print(f"Pushing file with {newImageName}")
        imageFileUrl = f'wsi_deid/item/{itemCopyToUnfiled["_id"]}/action/refile?imageId={newImageName}&tokenId={imageMeta["SampleID"]}'

        try:
            itemCopyOutput = gc.put(imageFileUrl)
            # deidMeta = {**itemCopyOutput["meta"]["deidUpload"], **imageMeta}
            print("-----------------" * 5)
            print(imageMeta)

            metaForDeidObject = {}
            for k, v in imageMeta.items():
                if k in bch.keysForBarcode:
                    metaForDeidObject[k] = v

            gc.addMetadataToItem(
                itemCopyOutput["_id"], {"deidUpload": metaForDeidObject}
            )
        except girder_client.HttpError as e:
            print(e)
        ## TO DO.. MOVE THIS TO THE DEBUG AREA


## TO DO-- DETERMINE IF I NEED TO SET A SIZE_LIMIT FOR THE CACHE


@callback(Output("mergedImageSet", "children"), Input("mergedItem_store", "data"))
def updateMergedDatatable(mergeddata):
    if mergeddata:
        for row in mergeddata:
            if row.get("match_result", None) == "Match":
                row["match_result_style"] = {"backgroundColor": "orange"}
            elif row["match_result"] == "NoMeta":
                row["match_result_style"] = {"backgroundColor": "orange"}
                # row["match_result_style"] = {"backgroundColor": "yellow"}
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
                    maxWidth=150,
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


### TO DO is DEFINE FUNCTION THAT DEALS WITH APPROVED / MERGED / ETC...


@callback(
    [
        Output("mergedItem_store", "data", allow_duplicate=True),
        Output("submit-deid-button", "disabled", allow_duplicate=True),
    ],
    Input("submit-deid-button", "n_clicks"),
    State("mergedItem_store", "data"),
    State("deid-flag-inputs", "value"),
    prevent_initial_call=True,
)
def submit_for_deid(n_clicks, data, deidFlags):
    if not n_clicks or not data:
        raise PreventUpdate

    ## Need to turn this into an array it it's null
    if not deidFlags:
        deidFlags = []
    print(len(data), "elements were received for processing")
    for row in data:
        print(row)
        curDsaPath = row.get("curDsaPath", None)
        print(curDsaPath)
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
            submitImageForDeId(row)
            row["deidStatus"] = "Submitted"
        else:
            row["deidStatus"] = "SKIPPED"

    processDeIDset(data, deidFlags)

    # Re-enable the button after processing
    return data, False


def processDeIDset(data, deID_flags):
    ### This will process a list of items in the DSA and move them through the deidentificaiton
    ## Workflow, which goes from submitted, into an availble to process, into a redacted folder
    print(deID_flags)
    # print(data)
    if "batchSubmit_atp" in deID_flags:
        atp_imageIds = [
            x["_id"] for x in data if x["deidStatus"] == "AvailableToProcess Folder"
        ]
        status = gc.put(f"wsi_deid/action/list/process?ids={json.dumps(atp_imageIds)}")
        print(status)
        print(atp_imageIds)

    if "batchSubmit_redacted" in deID_flags:
        redact_imageIds = [
            x["_id"] for x in data if x["deidStatus"] == "In Redacted Folder"
        ]
        status = gc.put(
            f"wsi_deid/action/list/finish?ids={json.dumps(redact_imageIds)}"
        )
        print(status)

        print(redact_imageIds)
    # gc.put(  /wsi_deid/action/list/{action}?ids=["",""]


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


# @callback(
#     [
#         Output("mergedItem_store", "data", allow_duplicate=True),
#         Output("submit-deid-button", "disabled", allow_duplicate=True),
#     ],
#     Input("submit-deid-button", "n_clicks"),
#     State("mergedItem_store", "data"),
#     State("submit-deid-button", "disabled"),
#     prevent_initial_call=True,
# )
# def submit_for_deid(n_clicks, data, is_disabled):
#     if not n_clicks or not data:
#         raise dash.exceptions.PreventUpdate

#     if is_disabled:
#         raise dash.exceptions.PreventUpdate

#     # Disable the button immediately while processing
#     is_button_disabled = True

#     for row in data:
#         if row["curDsaPath"]:
#             row["deidStatus"] = "Already Submitted"
#         elif row["match_result"] in ["Match", "NoMeta"]:
#             submitImageForDeId(row)
#             row["deidStatus"] = "Submitted"
#         else:
#             row["deidStatus"] = "SKIPPED"

#     # Re-enable the button after processing
#     is_button_disabled = False
#     return data, is_button_disabled


# def submit_for_deid(n_clicks, data, is_disabled):
#     if not n_clicks or not data:
#         raise dash.exceptions.PreventUpdate

#     if is_disabled:
#         raise dash.exceptions.PreventUpdate
#     # Disable the button immediately while processing
#     is_button_disabled = True


#     for row in data:
#         if row["curDsaPath"]:
#             row["deidStatus"] = "Already Submitted"
#         elif row["match_result"] in ["Match", "NoMeta"]:
#             submitImageForDeId(row)
#             row["deidStatus"] = "Submitted"
#         else:
#             row["deidStatus"] = "SKIPPED"
#     is_button_disabled = False
#     return data, False  # or any other message or result you want to display


# @callback(
#     Output("submit-deid-button", "disabled"),
#     Input("submit-deid-button", "n_clicks"),
#     State("submit-deid-button", "disabled"),
#     prevent_initial_call=True,
# )
# def disable_button(n_clicks, is_disabled):
#     if n_clicks > 0:
#         return True
#     return False
# dbc.Tooltip(
#     "You must be logged on to submit",
#     target="submit-deid-button-span",
# ),