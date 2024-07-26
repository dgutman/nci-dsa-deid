# Utility functions.
from dash import html
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import datetime
from jsonschema import Draft7Validator
from settings import SCHEMA, DSA_UNFILED_FOLDER
import os, json
import girder_client
import utils.barcodeHelpers as bch


def folder_div(collection_folder):
    if collection_folder["_modelType"] == "collection":
        level = 1
    else:
        level = 2

    return html.Div(
        [
            dmc.Button(
                collection_folder["name"],
                leftIcon=DashIconify(icon="material-symbols:folder", width=20),
                id={"type": "folder", "id": collection_folder["_id"], "level": level},
                n_clicks=0,
                variant="subtle",
                style={
                    "text-align": "left",
                    "margin-left": f"{20*level-25}px",
                    "padding": "2px 8px",
                    "font-size": "1rem",
                    "height": "20px",
                },
            ),
            html.Div(
                id={
                    "type": "subfolders",
                    "id": collection_folder["_id"],
                    "level": level,
                },
                style={"margin-left": f"{20*(level)-10}px"},
            ),
        ],
        style={
            "margin-top": "-4px",
            "margin-bottom": "-4px",
        },  # Adjust these values as needed
    )


def lookupDSAresource(gc, textPrefix, mode="prefix", limit=1):
    """This will use the girder_client to look for filenames in the DSA.  The app does not
    currently allow duplicate files to be created during the deID process.. this would make it extremely confusing
    to figure out what has and has not been deidentified"""
    searchOutput = gc.get(
        f'resource/search?q={textPrefix}&mode={mode}&limit={limit}&types=["item"]'
    )
    return searchOutput


def checkForExistingFile(gc, deidOutputFileName):
    ### By design, an image following de-identification can not duplicate an existing file name
    ## or it would be extremely difficult to figure out which version is which.. this looks for the
    ## filename on the DSA and returns a path to where the file is located
    ## Dependinog on the path, we can then trigger other options..
    searchStatus = gc.get(
        f'resource/search?q={deidOutputFileName}&mode=prefix&limit=1&types=["item"]'
    )

    if searchStatus:
        try:
            itemId = searchStatus["item"][0]["_id"]

            resourcePath = gc.get(f"resource/{itemId}/path?type=item")
            if resourcePath:
                return resourcePath
        except:
            pass

    return None


def process_row(gc, row, COLS_FOR_COPY, metadataDict):
    validator = Draft7Validator(SCHEMA)
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
        row["OutputFileName"] = os.path.splitext(row["name"])[0] + ".deid.svs"

        deidFileStatus = checkForExistingFile(gc, row["OutputFileName"])
        row["curDsaPath"] = deidFileStatus
        ## #Process / update DEID status here as well
        curDsaPath = row.get("curDsaPath", None)
        # print(curDsaPath)
        if curDsaPath:
            if curDsaPath.startswith("/collection/WSI DeID/Approved"):
                row["deidStatus"] = "In Approved Status"

            elif curDsaPath.startswith("/collection/WSI DeID/Redacted"):
                row["deidStatus"] = "In Redacted Folder"

            elif curDsaPath.startswith("/collection/WSI DeID/AvailableToProcess"):
                row["deidStatus"] = "AvailableToProcess Folder"

    if validator.is_valid(row):
        # print(row, "was validated??")
        row["valid"] = "Es Bueno"
    else:
        row["valid"] = "Es Malo"
        # print("Row was not valid:", row)

    return row


def submitImageForDeId(gc, row):
    # Your logic for submitting the image for DeID goes here
    ## So check if file is already un the unfiled Directory.. if so just use that..
    try:
        unfiledFolder = gc.get(f"resource/lookup?path=/collection{DSA_UNFILED_FOLDER}")
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
        newImageName = newImageName.replace(
            ".svs", ""
        )  ## Need to clarify with D Manthey where/how to avoid adding the extension twice

    try:
        fileUrl = f"resource/lookup?path=/collection/{newImagePath}.svs"  ## DEID adds extension during move
        fileExists = gc.get(fileUrl)
        fileExists = True
    except:
        fileExists = False

    if not fileExists:
        imageFileUrl = f'wsi_deid/item/{itemCopyToUnfiled["_id"]}/action/refile?imageId={newImageName}&tokenId={imageMeta["SampleID"]}'

        try:
            itemCopyOutput = gc.put(imageFileUrl)

            metaForDeidObject = {}
            for k, v in imageMeta.items():
                if k in bch.keysForBarcode:
                    metaForDeidObject[k] = v

            gc.addMetadataToItem(
                itemCopyOutput["_id"], {"deidUpload": metaForDeidObject}
            )
        except girder_client.HttpError as e:
            print(e)


def processDeIDset(gc, data, deID_flags):
    ### This will process a list of items in the DSA and move them through the deidentificaiton
    ## Workflow, which goes from submitted, into an availble to process, into a redacted folder
    if "batchSubmit_atp" in deID_flags:
        atp_imageIds = [
            x["_id"] for x in data if x["deidStatus"] == "AvailableToProcess Folder"
        ]
        status = gc.put(f"wsi_deid/action/list/process?ids={json.dumps(atp_imageIds)}")
        # print(status)
        # print(atp_imageIds)

    if "batchSubmit_redacted" in deID_flags:
        redact_imageIds = [
            x["_id"] for x in data if x["deidStatus"] == "In Redacted Folder"
        ]
        status = gc.put(
            f"wsi_deid/action/list/finish?ids={json.dumps(redact_imageIds)}"
        )
