import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import dash_mantine_components as dmc
import json, girder_client
import dash_ag_grid as dag
import json
import settings as s

from dash import callback, State, dcc, Output, Input, html, no_update
from dash.exceptions import PreventUpdate

import utils.barcodeHelpers as bch
import utils.deidHelpers as hlprs

from components.dsa_login_panel import getGc


## Trying to add diskcache functionality
def lookupDSAresource(textPrefix, mode="prefix", limit=1):
    """This will use the girder_client to look for filenames in the DSA.  The app does not
    currently allow duplicate files to be created during the deID process.. this would make it extremely confusing
    to figure out what has and has not been deidentified"""

    searchOutput = getGc().get(
        f'resource/search?q={textPrefix}&mode={mode}&limit={limit}&types=["item"]'
    )
    return searchOutput


def checkForExistingFile(deidOutputFileName):
    ### By design, an image following de-identification can not duplicate an existing file name
    ## or it would be extremely difficult to figure out which version is which.. this looks for the
    ## filename on the DSA and returns a path to where the file is located
    ## Dependinog on the path, we can then trigger other options..

    folders = (
        "/collection/WSI DeID/Approved",
        "/collection/WSI DeID/Redacted",
        "/collection/WSI DeID/AvailableToProcess",
    )

    searchStatus = lookupDSAresource(deidOutputFileName, limit=0)

    if searchStatus:
        for item in searchStatus.get("item", []):
            resourcePath = getGc().get(f"resource/{item['_id']}/path?type=item")

            if resourcePath.startswith((folders)):
                return resourcePath

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
            id="deid-flag-inputs",
        ),
    ],
    style={"display": "none"},
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


def getUnfiledFolder(gc):

    try:
        response = getGc().get("resource/lookup?path=/collection/WSI DeID/Unfiled")
    except:
        response = None

    if response:
        DSA_UNFILED_FOLDER = response["_id"]
        return DSA_UNFILED_FOLDER
    else:
        # Look for collection.
        try:
            response = getGc().get("resource/lookup?path=/collection/WSI DeID")
        except:
            # This breaks the app, by default your server should have this collection.
            raise Exception("WSI DeID collection not found, app cannot run this way.")

    return None


## TO DO.. ADD MORE LOGIC HERE
def submitImageForDeId(row):
    # Your logic for submitting the image for DeID goes here
    ## So check if file is already un the unfiled Directory.. if so just use that..
    # Get list of images in the unfiled folder.

    ## UNFILED FOLDER NEEDS TO BE LOOKED UP since it may be private..

    DSA_UNFILED_FOLDER = getUnfiledFolder(getGc())

    unfiledItemList = list(getGc().listItem(DSA_UNFILED_FOLDER))

    originalItemId_to_unfiledItemId = {}

    for x in unfiledItemList:
        originalItemId_to_unfiledItemId[x.get("copyOfItem", None)] = x

    if row["_id"] not in originalItemId_to_unfiledItemId:
        itemCopyToUnfiled = getGc().post(
            f'item/{row["_id"]}/copy?folderId={DSA_UNFILED_FOLDER}'
        )
    else:
        itemCopyToUnfiled = originalItemId_to_unfiledItemId[row["_id"]]

    imageMeta = row

    getGc().addMetadataToItem(itemCopyToUnfiled["_id"], {"deidUpload": row})

    newImageName = row["OutputFileName"]
    newImagePath = f'WSI DeID/AvailableToProcess/{row["SampleID"]}/{newImageName}'

    if newImageName.endswith(".svs"):
        # print("Updating new image path which is:", newImageName)
        newImageName = newImageName.replace(
            ".svs", ""
        )  ## Need to clarify with D Manthey where/how to avoid adding the extension twice
    # print("And now should be", newImageName)

    try:
        fileUrl = f"resource/lookup?path=/collection/{newImagePath}.svs"  ## DEID adds extension during move
        fileExists = getGc().get(fileUrl)
        fileExists = True
    except:
        fileExists = False
    ### See if the resource already exists  ..

    if not fileExists:
        # print(f"Pushing file with {newImageName}")
        imageFileUrl = f'wsi_deid/item/{itemCopyToUnfiled["_id"]}/action/refile?imageId={newImageName}&tokenId={imageMeta["SampleID"]}'

        try:
            itemCopyOutput = getGc().put(imageFileUrl)
            metaForDeidObject = {}
            for k, v in imageMeta.items():
                if k in bch.keysForBarcode:
                    metaForDeidObject[k] = v

            getGc().addMetadataToItem(
                itemCopyOutput["_id"], {"deidUpload": metaForDeidObject}
            )
        except girder_client.HttpError as e:
            print(e)
        ## TO DO.. MOVE THIS TO THE DEBUG AREA
        ### FURTHER TO DO IS MAKE SURE FILES DO NOT HAVE A (1) in their name... I find that annoying


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

            ## JC TO DO.. ADD SOME COLOR TO THE deID Status column in a less stupid way..

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
                                # "style": {"backgroundColor": "orange"},
                                "style": {"fontWeight": "bold", "color": "red"},
                            },
                            {
                                "condition": "params.value == 'Match'",
                                # "style": {
                                #     "backgroundColor": "purple",
                                #     "color": "white",
                                # },
                                "style": {"fontWeight": "bold", "color": "green"},
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
                    "enableCellTextSelection": True,
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
        Output("notifications-container", "children", allow_duplicate=True),
    ],
    Input("submit-deid-button", "n_clicks"),
    State("mergedItem_store", "data"),
    State("deid-flag-inputs", "value"),
    State("metadata_store", "data"),
    State("login-state", "data"),
    prevent_initial_call=True,
)
def submit_for_deid(n_clicks, data, deidFlags, metadataList, loginState):
    # This can only happen if there is an unfiled folder to check on.

    print(loginState, "is current login state..")
    if not loginState.get("logged_in", False):
        return (
            no_update,
            no_update,
            dmc.Notification(
                title="Warning",
                action="show",
                id="simple-notify",
                message="You must be logged in to submit for deid.",
                icon=DashIconify(icon="ic:round-celebration"),
            ),
        )

    if not n_clicks or not data:
        raise PreventUpdate

    ## Need to turn this into an array it it's null
    if not deidFlags:
        deidFlags = []
    for row in data:
        ### Check for valid metadata
        print("processing row", row)
        curDsaPath = row.get("curDsaPath", None)

        if row.get("valid") == "INVALID":
            row["deidStatus"] = "Invalid Metadata"
            continue

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
    return data, False, no_update


def processDeIDset(data, deID_flags):
    ### This will process a list of items in the DSA and move them through the deidentificaiton
    ## Workflow, which goes from submitted, into an availble to process, into a redacted folder

    if "batchSubmit_atp" in deID_flags:
        atp_imageIds = [
            x["_id"] for x in data if x["deidStatus"] == "AvailableToProcess Folder"
        ]
        status = getGc().put(
            f"wsi_deid/action/list/process?ids={json.dumps(atp_imageIds)}"
        )

    if "batchSubmit_redacted" in deID_flags:
        redact_imageIds = [
            x["_id"] for x in data if x["deidStatus"] == "In Redacted Folder"
        ]
        status = getGc().put(
            f"wsi_deid/action/list/finish?ids={json.dumps(redact_imageIds)}"
        )


@callback(Output("currentItemMacro", "src"), Input("merged-datagrid", "selectedRows"))
def displayMacroForSelectedRow(selected):
    if selected:
        thumbSrc = hlprs.get_thumbnail_as_b64(selected[0]["_id"])
        return thumbSrc
    ## TO FIX --- double check girder client token


@callback(
    Output("currentItemThumbnail", "src"), Input("merged-datagrid", "selectedRows")
)
def displayThumbnailForSelectedRow(selected):
    if selected:
        selected = selected[0]  ## Only returns a single row, but it's an array
        ### Hack for now  so I copy over the metadata needed..
        selected["meta"]["deidUpload"] = selected
        outputFileName = selected["meta"]["deidUpload"].get(
            "OutputFileName", "WrongTag"
        )
        deidBarCode = hlprs.add_barcode_to_image(
            selected, outputFileName, item=selected
        )

        encoded_image = hlprs.image_to_base64(deidBarCode)

        return f"data:image/png;base64,{encoded_image}"
