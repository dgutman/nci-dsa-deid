##Helper Functions to generate datamatrix barcodes
from PIL import ImageFont, Image, ImageDraw, ImageColor
from pylibdmtx.pylibdmtx import encode
import math, json
import PIL, os

try:
    from girder import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)

keysForBarcode = ["ASSAY", "BLOCK", "CASE", "INDEX", "PROJECT", "REPOSITORY", "STUDY"]

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


def _first_existing_path(*candidates):
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def _resolve_logo_path():
    """Path to the footer logo. Prefer $NCI_DSA_DEID_LOGO, then files next to this module."""
    return _first_existing_path(
        os.environ.get("NCI_DSA_DEID_LOGO"),
        os.path.join(_PACKAGE_DIR, "NCI-logo-300x165.jpg"),
        "/opt/nci-dsa-deid/nci_dsa_deid/NCI-logo-300x165.jpg",
        os.path.join(os.getcwd(), "NCI-logo-300x165.jpg"),
    )


def _resolve_font_path():
    return _first_existing_path(
        os.environ.get("NCI_DSA_DEID_FONT"),
        os.path.join(_PACKAGE_DIR, "DejaVuSansMono.ttf"),
        "/opt/nci-dsa-deid/nci_dsa_deid/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        os.path.join(os.getcwd(), "DejaVuSansMono.ttf"),
    )


logoImageFile = _resolve_logo_path()
# Always a concrete path for ImageFont.truetype (missing file => IOError and fallback in computeFontSize)
fontFile = _resolve_font_path() or os.path.join(_PACKAGE_DIR, "DejaVuSansMono.ttf")


def _load_logo(logo_path):
    if logo_path and os.path.isfile(logo_path):
        return Image.open(logo_path)
    logger.warning(
        "NCI label logo not found (expected a file at %r or set NCI_DSA_DEID_LOGO); using blank placeholder",
        logo_path,
    )
    return Image.new("RGB", (300, 165), color=(255, 255, 255))


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
            targetW, 0.15, line, fontFile=fontFile
        )
        max_textW = max(max_textW, textW)
        total_textH += textH

    # Adjust the title height based on the total height of all title lines
    titleH = int(math.ceil(total_textH * 1.40))

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

    logoImg = _load_logo(logoImageFile)

    # Dealing with barcode generation and placement...
    available_height = (
        targetW - titleH - logoImg.size[1]
    )  # space between title and logo

    # Generate barcode with error handling
    barcodeData = encode_barcode_string(item, keysForBarcode)
    
    if barcodeData:
        try:
            # Try to encode the barcode
            encoded = encode(barcodeData.encode("utf8"))
            
            if not encoded or not encoded.pixels:
                raise ValueError("pylibdmtx encode returned empty result")
            
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
            barcodeYoffset = (
                titleH + (available_height - barcode_resized.height) // 2
            )  ## Moving it down a bit more
            newImage.paste(barcode_resized, (barcodeXoffset, barcodeYoffset))
            print(barcodeYoffset, "is title height offset")
        except Exception as e:
            # If barcode encoding fails, log the error but continue without barcode
            print(f"Warning: Failed to encode barcode: {e}")
            print(f"Barcode data was: {barcodeData[:100]}...")  # Print first 100 chars for debugging
            # Continue without barcode - image will still have title and logo
    else:
        print("Warning: No barcode data available, skipping barcode generation")
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

    :returns: barcode string or None if metadata is missing/invalid
    """
    # Check if item has metadata
    if not item or "meta" not in item:
        print("Warning: Item missing 'meta' field, cannot generate barcode")
        return None
    
    if "deidUpload" not in item.get("meta", {}):
        print("Warning: Item missing 'deidUpload' metadata, cannot generate barcode")
        return None
    
    deidDict = item["meta"]["deidUpload"]
    ### We are placing the validated schema data at item.meta.deidUpload

    if not deidDict:
        print("Warning: 'deidUpload' metadata is empty, cannot generate barcode")
        return None

    barcodeText = ""
    for k in keys_to_encode:
        if k in deidDict and deidDict[k] is not None and deidDict[k] != "" and deidDict[k] != " ":
            barcodeText += "%s,%s|" % (k, deidDict[k])
    
    # Check if we have any data to encode
    if not barcodeText:
        print("Warning: No valid barcode data found in metadata")
        return None
    
    # Strip off the final |
    barcodeText = barcodeText[:-1]
    
    # Check barcode length - pylibdmtx has limits
    # DataMatrix can encode up to ~3116 numeric or ~2335 alphanumeric characters
    # But we want to keep it reasonable to avoid huge barcodes
    MAX_BARCODE_LENGTH = 2000  # Reasonable limit
    if len(barcodeText) > MAX_BARCODE_LENGTH:
        print(f"Warning: Barcode data too long ({len(barcodeText)} chars), truncating to {MAX_BARCODE_LENGTH}")
        barcodeText = barcodeText[:MAX_BARCODE_LENGTH]
    
    return barcodeText



def computeFontSize(
    targetW,
    fontSize,
    title,
    mode="RGB",
    minWidth=384,
    fontFile=fontFile,
    defaultFontSizeValue=8,
):
    ### Want to compute the biggest font that will fit in the allocated space for readbility

    # Build an empty image
    img = Image.new(mode, (minWidth, minWidth))
    imageDraw = ImageDraw.Draw(img)
    id = ImageDraw.Draw(img)
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
         
        textL, textT, textR, textB = imageDrawFont.getbbox(title)
        textW = textR - textL
        textH = abs(textB - textT)
        if textW == 0 or not textW:
            # Either skip the calculation or set a default value for fontSize
            textW = 0.2  # set this to a reasonable default

        # print(fontSize, "is font size..")
        if iter != 1 and (textW > targetW * 0.85 or textW < targetW * 0.85):
            fontSize = fontSize * targetW * 0.9 / textW

    return fontSize, textW, textH, imageDrawFont
