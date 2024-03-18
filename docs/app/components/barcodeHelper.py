##Helper Functions to generate datamatrix barcodes
from PIL import ImageFont, Image, ImageDraw, ImageColor
from pylibdmtx.pylibdmtx import encode
import math, json
import PIL, os

keysForBarcode = ["ASSAY", "BLOCK", "CASE", "INDEX", "PROJECT", "REPOSITORY", "STUDY"]

logoImageFile = "/opt/nci-dsa-deid/nci_dsa_deid/NCI-logo-300x165.jpg"

if os.path.isfile(logoImageFile):
    pass
else:
    logoImageFile = "./NCI-logo-300x165.jpg"
    ## During local testing the /opt path does not exist, so using local path


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
    logoImageFile=logoImageFile,
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
        fontSize, textW, textH, imageDrawFont = computeFontSize(
            targetW, 0.15, line, fontFile="./DejaVuSansMono.ttf"
        )
        max_textW = max(max_textW, textW)
        total_textH += textH

    # Adjust the title height based on the total height of all title lines
    titleH = int(math.ceil(total_textH * 1.35))

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

    barcodeData = encode_barcode_string(item, keysForBarcode)
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

    # ### Try to figure out the proper font size based on the size in pixels of the rendered text
    # ## using fontsize of 0.15 as a starting point
    # fontSize, textW, textH, imageDrawFont = computeFontSize(targetW, 0.15, title)
    # ## Setting fontsize of 0.15 as default

    # titleH = int(math.ceil(textH * 1.25))

    # ## I always want these to be a square..

    # if square and (w != h or (not previouslyAdded or w != targetW or h < titleH)):
    #     if targetW < h + titleH:
    #         targetW = h + titleH
    #     else:
    #         titleH = targetW - h

    # newImage = PIL.Image.new(mode=mode, size=(targetW, h + titleH), color=background)
    # # newImage.paste(lblImage, (int((targetW - w) / 2), titleH))

    # imageDraw = ImageDraw.Draw(newImage)
    # imageDraw.rectangle((0, 0, targetW, titleH), fill=background, outline=None, width=0)
    # imageDraw.text(
    #     xy=(int((targetW - textW) / 2), int((titleH - textH) / 2)),
    #     text=title,
    #     fill=textColor,
    #     font=imageDrawFont,
    # )

    # barcodeData = encode_barcode_string(item, keysForBarcode)
    # encoded = encode(barcodeData.encode("utf8"))
    # img = Image.frombytes("RGB", (encoded.width, encoded.height), encoded.pixels)
    # ## Since I know the width, I can figure out the encoded width, and then try and center the barcode
    # barcodeXoffset = int((targetW - encoded.width) / 2)
    # newImage.paste(img, (barcodeXoffset, int(minWidth / 6)))

    # ## TO DO make this a global parameter
    # # logoImageFile = "/opt/nci-dsa-deid/nci_dsa_deid/NCI-logo-300x165.jpg"
    # logoImg = Image.open(logoImageFile)

    # logoOffsetX = int((targetW - logoImg.size[0]) / 2)
    # logoOffsetY = int(targetW - logoImg.size[1])
    # newImage.paste(logoImg, (logoOffsetX, logoOffsetY))

    # return newImage


def encode_barcode_string(item, keys_to_encode):
    """
    This encodes a barcode as a comma and pipe delimited string given an input dictionary
    and the set of keys from the dictionary that should be encoded

    :param item: this is the item object from girder, so contains metadata, as well as large image info
    :param keys_to_encode This is an array of keys that should be included/encoded into the 2d Datamatrix

    TODO: Figure out the max # of characters that can be in the output string before the barcode generation
    starts getting out of hand, I don't want a 4kx4k barcode

    """
    # print(item)
    deidDict = item["meta"]["deidUpload"]
    ### We are placing the validated schema data at item.meta.deidUpload

    barcodeText = ""
    for k in keys_to_encode:
        if k in deidDict:
            barcodeText += "%s,%s|" % (k, deidDict[k])
    # print(barcodeText)
    return barcodeText[:-1]  ## Strip off the final |


def computeFontSize(
    targetW,
    fontSize,
    title,
    mode="RGB",
    minWidth=384,
    fontFile="DejaVuSansMono.ttf",
    defaultFontSizeValue=8,
):
    ### Want to compute the biggest font that will fit in the allocated space for readbility

    # Build an empty image
    img = Image.new(mode, (minWidth, minWidth))
    imageDraw = ImageDraw.Draw(img)

    for iter in range(3, 0, -1):
        try:
            imageDrawFont = ImageFont.truetype(
                fontFile,
                size=int(fontSize * targetW),
            )
        except IOError:
            try:
                imageDrawFont = PIL.ImageFont.truetype(size=int(fontSize * targetW))
            except IOError:
                imageDrawFont = PIL.ImageFont.load_default()
        textW, textH = imageDraw.textsize(title, imageDrawFont)

        if textW == 0 or not textW:
            # Either skip the calculation or set a default value for fontSize
            textW = 0.2  # set this to a reasonable default

        # print(fontSize, "is font size..")
        if iter != 1 and (textW > targetW * 0.95 or textW < targetW * 0.85):
            fontSize = fontSize * targetW * 0.9 / textW

    return fontSize, textW, textH, imageDrawFont
