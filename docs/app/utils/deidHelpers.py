import os
from PIL import Image, ImageDraw
import io, base64, math
import utils.barcodeHelpers as bch
from io import BytesIO
import PIL
from components.dsa_login_panel import getGc
from pylibdmtx.pylibdmtx import encode

import jsonschema
from jsonschema import Draft7Validator
import settings as s
import pandas as pd
from dash import html
import datetime

import io, base64, json, jsonschema, random, datetime
import dash_ag_grid as dag
import config
import base64
import numpy as np


def read_file_from_system(filename, filetype):
    if "csv" in filetype:
        return pd.read_csv(filename)
    elif "xls" in filetype:
        return pd.read_excel(filename)
    else:
        raise ValueError("Unsupported file type.")


schema = s.SCHEMA


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


def read_file_from_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)

    if "csv" in filename:
        return pd.read_csv(io.StringIO(decoded.decode("utf-8")), on_bad_lines="skip")
    elif "xls" in filename:
        return pd.read_excel(io.BytesIO(decoded))
    else:
        raise ValueError("Unsupported file type.")


def split_into_chunks(s, max_length=40):
    return [s[i : i + max_length] for i in range(0, len(s), max_length)]


def add_barcode_to_image(
    image,
    title,
    previouslyAdded=False,
    minWidth=512,
    background="#ffffff",
    textColor="#000000",
    square=True,
    item=None,
    logoImageFile="NCI-logo-300x165.jpg",
):
    """
    Add both a title and a barcode to an image.  If the image doesn't exist, a new image is made
    the minimum width and appropriate height.  If the image does exist, a bar
    is added at its top to hold the title.  If an existing image is smaller
    than minWidth, it is pillarboxed to the minWidth.

    :param image: a PIL image or None.
    :param title: a text string.
    :param previouslyAdded: if true and modifying an image, don't allocate more
        space for the title; overwrite the top of the image instead.
    :param minWidth: the minimum width for the new image.
    :param background: the background color of the title and any necessary
        pillarbox.
    :param textColor: the color of the title text.
    :param square: if True, output a square image.
    : param item: Returns the internal metadata for the image item
    :returns: a PIL image.
    """

    mode = "RGB"

    ## While I am passed the image, and in the future may want to scan it or do something with it
    ## In this new version, I am simply creating a new label image and throwing out the old one
    lblImage = Image.new(mode, (minWidth, minWidth))

    w, h = lblImage.size
    background = PIL.ImageColor.getcolor(background, mode)
    textColor = PIL.ImageColor.getcolor(textColor, mode)
    targetW = max(minWidth, w)
    fontSize = 0.15
    imageDraw = PIL.ImageDraw.Draw(lblImage)

    ### Try to figure out the proper font size based on the size in pixels of the rendered text
    ## using fontsize of 0.15 as a starting point
    # Split the title into multiple lines if necessary
    title_lines = split_into_chunks(title)

    # print(title_lines, "was passed..")
    # Compute the font size and text width for each line
    max_textW = 0
    total_textH = 0
    for line in title_lines:
        fontSize, textW, textH, imageDrawFont = bch.computeFontSize(
            targetW, 0.15, line, fontFile="./DejaVuSansMono.ttf"
        )
        max_textW = max(max_textW, textW)
        total_textH += textH

    # Adjust the title height based on the total height of all title lines
    titleH = int(math.ceil(total_textH * 1.35))
    if titleH > 900:
        titleH = 52  ### Need to empierically determine max Height..
    ## I always want these to be a square..

    if square and (w != h or (not previouslyAdded or w != targetW or h < titleH)):
        if targetW < h + titleH:
            targetW = h + titleH
        else:
            titleH = targetW - h

    newImage = PIL.Image.new(mode=mode, size=(targetW, h + titleH), color=background)
    # newImage.paste(lblImage, (int((targetW - w) / 2), titleH))

    imageDraw = ImageDraw.Draw(newImage)
    imageDraw.rectangle((0, 0, targetW, titleH), fill=background, outline=None, width=0)

    # Draw each title line on the image
    y_offset = int((titleH - total_textH) / 2)
    for line in title_lines:
        imageDraw.text(
            xy=(int((targetW - max_textW) / 2), y_offset),
            text=line,
            fill=textColor,
            font=imageDrawFont,
        )
        y_offset += textH

    ## TO DO make this a global parameter

    logoImg = Image.open(logoImageFile)

    # Dealing with barcode generation and placement...
    available_height = (
        targetW - titleH - logoImg.size[1]
    )  # space between title and logo

    barcodeData = bch.encode_barcode_string(item, bch.keysForBarcode)
    encoded = encode(barcodeData.encode("utf8"))
    img = Image.frombytes("RGB", (encoded.width, encoded.height), encoded.pixels)

    barcode_aspect_ratio = encoded.width / encoded.height
    max_barcode_width = int(available_height * barcode_aspect_ratio)

    # If the barcode width after resizing exceeds the target width, adjust the available height
    if max_barcode_width > targetW:
        available_height = int(targetW / barcode_aspect_ratio)
        max_barcode_width = targetW

    barcode_resized = img.resize((max_barcode_width, available_height))

    ## Since I know the width, I can figure out the encoded width, and then try and center the barcode
    # Place the resized barcode in the center
    barcodeXoffset = (targetW - barcode_resized.width) // 2
    barcodeYoffset = titleH + (available_height - barcode_resized.height) // 2
    newImage.paste(barcode_resized, (barcodeXoffset, barcodeYoffset))
    # barcodeXoffset = int((targetW - encoded.width) / 2)
    # newImage.paste(img, (barcodeXoffset, int(minWidth / 6)))

    logoOffsetX = int((targetW - logoImg.size[0]) / 2)
    logoOffsetY = int(targetW - logoImg.size[1])
    newImage.paste(logoImg, (logoOffsetX, logoOffsetY))

    return newImage


def create_image():
    # Create a new image with white background
    img = Image.new("RGB", (300, 300), color="white")

    # Get drawing context
    d = ImageDraw.Draw(img)

    # Draw a blue rectangle and some text on the image
    d.rectangle([(50, 50), (250, 250)], fill="blue")
    d.text((100, 150), "Hello from Pillow", fill="white")
    return img


def image_to_base64(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def pull_thumbnail_array(item_id, height=1000, encoding="PNG"):
    """
    Gets thumbnail image associated with provided item_id and with specified height
    The aspect ratio is retained, so the width may not be equal to the height
    Thumbnail is returned as a numpy array, after dropping alpha channel
    Thumbnail encoding is specified as PNG by default
    """
    thumb_download_endpoint = (
        f"/item/{item_id}/tiles/thumbnail?encoding={encoding}&height={height}"
    )
    try:
        thumb = getGc().get(thumb_download_endpoint, jsonResp=False).content
        thumb = np.array(Image.open(BytesIO(thumb)))
        # dropping alpha channel and keeping only rgb
        thumb = thumb[:, :, :3]
    except:
        thumb = np.ones((1000, 1000, 3), dtype=np.uint8)
        # print(thumb)
    return thumb


def get_thumbnail_as_b64(item_id=None, thumb_array=False, height=256, encoding="PNG"):
    """
    If thumb_array provided, just converts, otherwise will fetch required thumbnail array

    Fetches thumbnail image associated with provided item_id and with specified height
    The aspect ratio is retained, so the width may not be equal to the height

    Thumbnail is returned as b64 encoded string
    """
    thumb_download_endpoint = (
        f"item/{item_id}/tiles/thumbnail?encoding={encoding}"  # &height={height}"
    )
    thumb = getGc().get(thumb_download_endpoint, jsonResp=False).content

    base64_encoded = base64.b64encode(thumb).decode("utf-8")

    # ## TO DO: Cache this?
    pickledItem = getGc().get(
        f"item/{item_id}/tiles/thumbnail?encoding=pickle", jsonResp=False
    )

    # ## Need to have or cache the baseImage size as well... another feature to add
    import pickle

    baseImage_as_np = pickle.loads(pickledItem.content)

    img_io = BytesIO()
    Image.fromarray(baseImage_as_np).convert("RGB").save(img_io, "PNG", quality=95)
    b64image = base64.b64encode(img_io.getvalue()).decode("utf-8")
    html_img_src = f"data:image/png;base64,{b64image}"

    return html_img_src


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
            invalid_cols.append(*e.path)
        # print(invalid_cols)
        if invalid_cols:
            print(",".join(invalid_cols))
            df.at[i, "valid"] = False
            df.at[i, "error_cols"] = str(invalid_cols)
    return df


# # def print_all_errors(error_tree):
# #     for error in error_tree.errors:
# #         print(f"Error at {list(error.path)}: {error.message}")


# # wsiDeidFolderPathsForCleanup = [
# #     "/WSI DeID/Unfiled",
# #     "/WSI DeID/Redacted",
# #     "/WSI DeID/Reports/Import Job Reports",
# #     "/WSI DeID/Redacted",
# #     "/WSI DeID/Approved",
# # ]


# # def cleanupFoldersByPath(gc, folderPathList):
# #     """This converts a list of paths that are the relative girder path
# #     and converts them into actual girder folder objects.. i.e. gives me the _id field
# #     I need to access them.  This should also make it easier ti switch between systems
# #     since I don't have to hard code _ids which frequently change"""
# #     for fpl in folderPathList:
# #         f = gc.get(f"resource/lookup?path=/collection{fpl}")
# #         results = cleanupFolder(gc, f["_id"])
# #         print(
# #             f'Deleted {results[0]} items and {results[1]} folders in folder {f["name"]}'
# #         )

# #     return html.Div(
# #         [
# #             html.H5(filename),
# #             html.H6(datetime.datetime.now()),
# #             dag.AgGrid(
# #                 rowData=df.to_dict("records"),
# #                 columnDefs=[{"headerName": i, "field": i} for i in df.columns],
# #                 id="metadataTable",
# #             ),
# #         ]
# #     )

# # def cleanupFolder(gc, folderId):
# #     """This will remove all items and folders from a given input folderID"""
# #     ### Get all thei the items in the current Folder and remove them
# #     itemsDeleted = 0
# #     for i in gc.listItem(folderId):
# #         gc.delete(f'item/{i["_id"]}')
# #         itemsDeleted += 1

# #     foldersDeleted = 0
# #     for f in gc.listFolder(folderId):
# #         gc.delete(f'folder/{f["_id"]}')
# #         foldersDeleted += 1

# #     return itemsDeleted, foldersDeleted
