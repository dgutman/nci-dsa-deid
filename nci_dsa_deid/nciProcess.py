import base64
import copy
import io
import math
import os
import re
import subprocess
import threading
import time
import xml.etree.ElementTree

import numpy
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageOps

# import pyvips
# import tifftools
from girder import logger
from girder.models.folder import Folder
from girder.models.item import Item
from girder.models.setting import Setting
from girder_large_image.models.image_item import ImageItem
from large_image.tilesource import dictToEtree

from . import barcodeHelpers

# from . import config

# from .constants import PluginSettings, TokenOnlyPrefix

## Will probably overload title and just make it pass the entire string I am interested in..

import json
from pylibdmtx.pylibdmtx import encode


###'2.25.' + str(uuid.uuid4().int)   Generate a DICOM UID


def add_barcode_to_image(
    image, title, dataDict, previouslyAdded=False, minWidth=384, background="#000000", textColor="#ffffff", square=True, item=None
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
    :returns: a PIL image.
    """
    print(item)

    mode = "RGB"
    if image is None:
        image = PIL.Image.new(mode, (0, 0))
    image = image.convert(mode)
    w, h = image.size
    background = PIL.ImageColor.getcolor(background, mode)
    textColor = PIL.ImageColor.getcolor(textColor, mode)
    targetW = max(minWidth, w)
    fontSize = 0.15
    imageDraw = PIL.ImageDraw.Draw(image)
    for iter in range(3, 0, -1):
        try:
            imageDrawFont = PIL.ImageFont.truetype(
                font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size=int(fontSize * targetW)
            )
        except IOError:
            try:
                imageDrawFont = PIL.ImageFont.truetype(size=int(fontSize * targetW))
            except IOError:
                imageDrawFont = PIL.ImageFont.load_default()
        textW, textH = imageDraw.textsize(title, imageDrawFont)
        if iter != 1 and (textW > targetW * 0.95 or textW < targetW * 0.85):
            fontSize = fontSize * targetW * 0.9 / textW
    titleH = int(math.ceil(textH * 1.25))
    if square and (w != h or (not previouslyAdded or w != targetW or h < titleH)):
        if targetW < h + titleH:
            targetW = h + titleH
        else:
            titleH = targetW - h
    if previouslyAdded and w == targetW and h >= titleH:
        newImage = image.copy()
    else:
        newImage = PIL.Image.new(mode=mode, size=(targetW, h + titleH), color=background)
        newImage.paste(image, (int((targetW - w) / 2), titleH))
    imageDraw = PIL.ImageDraw.Draw(newImage)
    imageDraw.rectangle((0, 0, targetW, titleH), fill=background, outline=None, width=0)
    imageDraw.text(
        xy=(int((targetW - textW) / 2), int((titleH - textH) / 2)), text=title, fill=textColor, font=imageDrawFont
    )
    jsonString = json.dumps({"HELLO": "WORLD", "SCOTT": "ISTALL", "HOW": "AREYOU"})

    jsonString = json.dumps(item['meta']['deidUpload']) ## Add checks

    encoded = encode(jsonString.encode("utf8"))
    img = PIL.Image.frombytes("RGB", (encoded.width, encoded.height), encoded.pixels)

    return img


# def get_generated_title(item):
#     """
#     Given an item with possible metadata and redactions, return the desired
#     title.

#     :param item: a Girder item.
#     :returns: a title.
#     """
#     redactList = get_redact_list(item)
#     title = os.path.splitext(item['name'])[0]
#     for key in {
#             'internal;openslide;aperio.Title',
#             'internal;openslide;hamamatsu.Reference',
#             'internal;xml;PIIM_DP_SCANNER_OPERATOR_ID',
#             'internal;xml;PIM_DP_UFS_BARCODE'}:
#         if redactList['metadata'].get(key):
#             return redactList['metadata'].get(key)['value']
#     # TODO: Pull from appropriate 'meta' if not otherwise present
#     return title


def determine_format(tileSource):
    """
    Given a tile source, return the vendor format.

    :param tileSource: a large_image tile source.
    :returns: the vendor or None if unknown.
    """
    metadata = tileSource.getInternalMetadata() or {}
    if tileSource.name == "openslide":
        if metadata.get("openslide", {}).get("openslide.vendor") in ("aperio", "hamamatsu"):
            return metadata["openslide"]["openslide.vendor"]
    if "xml" in metadata and any(k.startswith("PIM_DP_") for k in metadata["xml"]):
        return "philips"
    return None


# def get_standard_redactions(item, title):
#     """
#     Produce a standardize redaction list based on format.

#     :param item: a Girder item.
#     :param title: the new title of the image.
#     :returns: a redactList.
#     """
#     tileSource = ImageItem().tileSource(item)
#     sourcePath = tileSource._getLargeImagePath()
#     tiffinfo = tifftools.read_tiff(sourcePath)
#     ifds = tiffinfo['ifds']
#     func = None
#     format = determine_format(tileSource)
#     if format is not None:
#         func = globals().get('get_standard_redactions_format_' + format)
#     if func:
#         redactList = func(item, tileSource, tiffinfo, title)
#     else:
#         redactList = {
#             'images': {},
#             'metadata': {},
#         }
#     for key in {'DateTime'}:
#         tag = tifftools.Tag[key].value
#         if tag in ifds[0]['tags']:
#             value = ifds[0]['tags'][tag]['data']
#             if len(value) >= 10:
#                 value = value[:5] + '01:01' + value[10:]
#             else:
#                 value = None
#             redactList['metadata']['internal;openslide;tiff.%s' % key] = (
#                 generate_system_redaction_list_entry(value)
#             )
#     # Make, Model, Software?
#     for key in {'Copyright', 'HostComputer'}:
#         tag = tifftools.Tag[key].value
#         if tag in ifds[0]['tags']:
#             redactList['metadata']['internal;openslide;tiff.%s' % key] = {
#                 'value': None, 'automatic': True}
#     return redactList



# def redact_image_area(image, geojson):
#     """
#     Redact an area from a PIL image.

#     :param image: a PIL image.
#     :param geojson: area to be redacted in geojson format.
#     """
#     width, height = image.size
#     polygon_svg = polygons_to_svg(geojson_to_polygons(geojson), width, height)
#     svg_image = pyvips.Image.svgload_buffer(polygon_svg.encode())
#     buffer = io.BytesIO()
#     image.save(buffer, 'TIFF')
#     vips_image = pyvips.Image.new_from_buffer(buffer.getvalue(), '')
#     redacted_image = vips_image.composite([svg_image], pyvips.BlendMode.OVER)
#     if redacted_image.bands > 3:
#         redacted_image = redacted_image[:3]
#     elif redacted_image.bands == 2:
#         redacted_image = redacted_image[:1]
#     redacted_data = redacted_image.write_to_buffer('.tiff')
#     redacted_image = PIL.Image.open(io.BytesIO(redacted_data))
#     return redacted_image


# def redact_item(item, tempdir):
#     """
#     Redact a Girder item.  Based on the redact metadata, determine what
#     redactions are necessary and perform them.

#     :param item: a Girder large_image item.  The file in this item will be
#         replaced with the redacted version.  The caller should copy the item
#         before running this script, as otherwise the original file may be
#         removed from the system.
#     :param tempdir: a temporary directory to put all work files and the final
#         result.
#     :returns: the generated filepath.  The filepath ends in the original
#         extension, its name is not important.
#     :returns: a dictionary of information including 'mimetype'.
#     """
#     previouslyRedacted = bool(item.get('meta', {}).get('redacted'))
#     redactList = get_redact_list(item)
#     newTitle = get_generated_title(item)
#     tileSource = ImageItem().tileSource(item)
#     labelImage = None
#     label_geojson = redactList.get('images', {}).get('label', {}).get('geojson')
#     if (('label' not in redactList['images'] and not config.getConfig('always_redact_label')) or
#             label_geojson is not None):
#         try:
#             labelImage = PIL.Image.open(io.BytesIO(tileSource.getAssociatedImage('label')[0]))
#             ImageItem().removeThumbnailFiles(item)
#         except Exception:
#             pass
#     if label_geojson is not None and labelImage is not None:
#         labelImage = redact_image_area(labelImage, label_geojson)
#     if config.getConfig('add_title_to_label'):
#         labelImage = add_title_to_image(labelImage, newTitle, previouslyRedacted)
#     macroImage = None
#     macro_geojson = redactList.get('images', {}).get('macro', {}).get('geojson')
#     redact_square_default = ('macro' not in redactList['images'] and
#                              config.getConfig('redact_macro_square'))
#     redact_square_manual = ('macro' in redactList['images'] and
#                             redactList['images']['macro'].get('square'))
#     redact_square = redact_square_default or redact_square_manual
#     if redact_square or macro_geojson:
#         try:
#             macroImage = PIL.Image.open(io.BytesIO(tileSource.getAssociatedImage('macro')[0]))
#             ImageItem().removeThumbnailFiles(item)
#         except Exception:
#             pass
#     if macroImage is not None:
#         if redact_square:
#             macroImage = redact_topleft_square(macroImage)
#         elif macro_geojson:
#             macroImage = redact_image_area(macroImage, macro_geojson)
#     format = determine_format(tileSource)
#     func = None
#     if format is not None:
#         fadvise_willneed(item)
#         func = globals().get('redact_format_' + format)
#     if func is None:
#         raise Exception('Cannot redact this format.')
#     file, mimetype = func(item, tempdir, redactList, newTitle, labelImage, macroImage)
#     info = {
#         'format': format,
#         'model': model_information(tileSource, format),
#         'mimetype': mimetype,
#         'redactionCount': {
#             key: len([k for k, v in redactList[key].items() if v['value'] is None])
#             for key in redactList if key != 'area'},
#         'fieldCount': {
#             'metadata': metadata_field_count(tileSource, format, redactList),
#             'images': len(tileSource.getAssociatedImagesList()),
#         },
#     }
#     return file, info




# def get_deid_field_dict(item):
#     """
#     Return a dictionary with custom fields from the DeID Upload metadata.

#     :param item: the item with data.
#     :returns: a dictionary of key-vlaue pairs.
#     """
#     deid = item.get('meta', {}).get('deidUpload', {})
#     if not isinstance(deid, dict):
#         deid = {}
#     result = {}
#     for k, v in deid.items():
#         result['CustomField.%s' % k] = str(v).replace('|', ' ')
#     return result


# def get_deid_field(item, prefix=None):
#     """
#     Return a text field with the DeID Upload metadata formatted for storage.

#     :param item: the item with data.
#     :returns: the text field.
#     """
#     from . import __version__

#     version = 'DSA Redaction %s' % __version__
#     if prefix and prefix.strip():
#         if 'DSA Redaction' in prefix:
#             prefix.split('DSA Redaction')[0].strip()
#         if prefix:
#             prefix = prefix.strip() + '\n'
#     else:
#         prefix = ''
#     return prefix + version + '\n' + '|'.join([
#         '%s = %s' % (k, v) for k, v in sorted(get_deid_field_dict(item).items())])


# def add_deid_metadata(item, ifds):
#     """
#     Add deid metadata to the Software tag.

#     :param item: the item to adjust.
#     :param ifds: a list of ifd info records.  Tags may be added or modified.
#     """
#     ifds[0]['tags'][tifftools.Tag.Software.value] = {
#         'datatype': tifftools.Datatype.ASCII,
#         'data': get_deid_field(item),
#     }


def geojson_to_polygons(geojson):
    """
    Convert geojson as generated by geojs's annotation layer.

    :param geojson: geojson record.
    :returns: an array of polygons, each of which is an array of points.
    """
    polys = []
    for feature in geojson["features"]:
        if feature.get("geometry", {}).get("type") == "Polygon":
            polys.append(feature["geometry"]["coordinates"])
    return polys


def polygons_to_svg(polygons, width, height, cropAllowed=True, offsetx=0, offsety=0):
    """
    Convert a list of polygons to an svg record.

    :param polygons: a list of polygons.
    :param width: width of the image.
    :param height: height of the image.
    :param cropAllowed: if True, the final width and height may be smaller than
        that specified if the polygons don't cover the right or bottom edge.
    :param offsetx: if set, deduct this value from all polygon coordinates.
    :param offsety: if set, deduct this value from all polygon coordinates.
    """
    if offsetx or offsety:
        polygons = [[[[pt[0] - offsetx, pt[1] - offsety] for poly in polygons for loop in poly for pt in loop]]]
    if cropAllowed:
        width = max(1, min(width, int(math.ceil(max(pt[0] for poly in polygons for loop in poly for pt in loop)))))
        height = max(1, min(height, int(math.ceil(max(pt[1] for poly in polygons for loop in poly for pt in loop)))))
    svg = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    for poly in polygons:
        svg.append('<path fill-rule="evenodd" fill="black" d="')
        for loop in poly:
            svg.append("M ")
            svg.append(" L ".join([f"{pt[0]},{pt[1]}" for pt in loop]))
            svg.append(" z")
        svg.append('"/>')
    svg.append("</svg>")
    svg = "".join(svg)
    return svg


# def redact_format_aperio(item, tempdir, redactList, title, labelImage, macroImage):
#     """
#     Redact aperio files.

#     :param item: the item to redact.
#     :param tempdir: a directory for work files and the final result.
#     :param redactList: the list of redactions (see get_redact_list).
#     :param title: the new title for the item.
#     :param labelImage: a PIL image with a new label image.
#     :param macroImage: a PIL image with a new macro image.  None to keep or
#         redact the current macro image.
#     :returns: (filepath, mimetype) The redacted filepath in the tempdir and
#         its mimetype.
#     """
#     import large_image_source_tiff.girder_source

#     tileSource = ImageItem().tileSource(item)
#     sourcePath = tileSource._getLargeImagePath()
#     logger.info('Redacting aperio file %s', sourcePath)
#     tiffinfo = tifftools.read_tiff(sourcePath)
#     ifds = tiffinfo['ifds']
#     if redactList.get('area', {}).get('_wsi', {}).get('geojson'):
#         ifds = redact_format_aperio_philips_redact_wsi(
#             tileSource, ifds, redactList['area']['_wsi']['geojson'], tempdir)
#         ImageItem().removeThumbnailFiles(item)
#     aperioValues = aperio_value_list(item, redactList, title)
#     imageDescription = '|'.join(aperioValues)
#     # We expect aperio to have the full resolution image in directory 0, the
#     # thumbnail in directory 1, lower resolutions starting in 2, and label and
#     # macro images in other directories.  Confirm this -- our tiff reader will
#     # report the directories used for the full resolution.
#     tiffSource = large_image_source_tiff.girder_source.TiffGirderTileSource(item)
#     mainImageDir = [dir._directoryNum for dir in tiffSource._tiffDirectories[::-1] if dir]
#     associatedImages = tileSource.getAssociatedImagesList()
#     if mainImageDir != [d + (1 if d and 'thumbnail' in associatedImages else 0)
#                         for d in range(len(mainImageDir))]:
#         raise Exception('Aperio TIFF directories are not in the expected order.')
#     firstAssociatedIdx = max(mainImageDir) + 1
#     # Set new image description
#     ifds[0]['tags'][tifftools.Tag.ImageDescription.value] = {
#         'datatype': tifftools.Datatype.ASCII,
#         'data': imageDescription,
#     }
#     # redact or adjust thumbnail
#     if 'thumbnail' in associatedImages:
#         if 'thumbnail' in redactList['images']:
#             ifds.pop(1)
#             firstAssociatedIdx -= 1
#         else:
#             thumbnailComment = ifds[1]['tags'][tifftools.Tag.ImageDescription.value]['data']
#             thumbnailDescription = '|'.join(thumbnailComment.split('|', 1)[0:1] + aperioValues[1:])
#             ifds[1]['tags'][tifftools.Tag.ImageDescription.value][
#                 'data'] = thumbnailDescription
#     # redact other images
#     for idx in range(len(ifds) - 1, 0, -1):
#         ifd = ifds[idx]
#         key = None
#         keyparts = ifd['tags'].get(tifftools.Tag.ImageDescription.value, {}).get(
#             'data', '').split('\n', 1)[-1].strip().split()
#         if len(keyparts) and keyparts[0].lower() and not keyparts[0][0].isdigit():
#             key = keyparts[0].lower()
#         if (key is None and ifd['tags'].get(tifftools.Tag.NewSubfileType.value) and
#                 ifd['tags'][tifftools.Tag.NewSubfileType.value]['data'][0] &
#                 tifftools.Tag.NewSubfileType.bitfield.ReducedImage.value):
#             key = 'label' if ifd['tags'][
#                 tifftools.Tag.NewSubfileType.value]['data'][0] == 1 else 'macro'
#         if key in redactList['images'] or key == 'label' or (key == 'macro' and macroImage):
#             ifds.pop(idx)
#     # Add back label and macro image
#     if macroImage:
#         redact_format_aperio_add_image(
#             'macro', macroImage, ifds, firstAssociatedIdx, tempdir, aperioValues)
#     if labelImage:
#         redact_format_aperio_add_image(
#             'label', labelImage, ifds, firstAssociatedIdx, tempdir, aperioValues)
#     # redact general tiff tags
#     redact_tiff_tags(ifds, redactList, title)
#     add_deid_metadata(item, ifds)
#     outputPath = os.path.join(tempdir, 'aperio.svs')
#     tifftools.write_tiff(ifds, outputPath)
#     logger.info('Redacted aperio file %s as %s', sourcePath, outputPath)
#     return outputPath, 'image/tiff'


# def redact_format_aperio_add_image(key, image, ifds, firstAssociatedIdx, tempdir, aperioValues):
#     """
#     Add a label or macro image to an aperio file.

#     :param key: either 'label' or 'macro'
#     :param image: a PIL image.
#     :param ifds: ifds of output file.
#     :param firstAssociatedIdx: ifd index of first associated image.
#     :param tempdir: a directory for work files and the final result.
#     :param aperioValues: a list of aperio metadata values.
#     """
#     imagePath = os.path.join(tempdir, '%s.tiff' % key)
#     image.save(imagePath, format='tiff', compression='jpeg', quality=90)
#     imageinfo = tifftools.read_tiff(imagePath)
#     imageDescription = aperioValues[0].split('\n', 1)[1] + '\n%s %dx%d' % (
#         key, image.width, image.height)
#     imageinfo['ifds'][0]['tags'][tifftools.Tag.ImageDescription.value] = {
#         'datatype': tifftools.Datatype.ASCII,
#         'data': imageDescription
#     }
#     imageinfo['ifds'][0]['tags'][tifftools.Tag.NewSubfileType] = {
#         'data': [9 if key == 'macro' else 1], 'datatype': tifftools.Datatype.LONG}
#     imageinfo['ifds'][0]['tags'][tifftools.Tag.ImageDepth] = {
#         'data': [1], 'datatype': tifftools.Datatype.SHORT}
#     ifds[firstAssociatedIdx:firstAssociatedIdx] = imageinfo['ifds']


def read_ts_as_vips(ts):
    """
    Read a tile source into a vips image.

    :param ts: a large image tile source.
    :returns: a vips image.
    """
    from large_image_converter import (
        _convert_large_image_tile,
        _drain_pool,
        _get_thread_pool,
        _import_pyvips,
        _pool_add,
    )

    _import_pyvips()
    _iterTileSize = 4096
    strips = []
    pool = _get_thread_pool()
    tasks = []
    tilelock = threading.Lock()
    for tile in ts.tileIterator(tile_size=dict(width=_iterTileSize)):
        _pool_add(tasks, (pool.submit(_convert_large_image_tile, tilelock, strips, tile),))
    _drain_pool(pool, tasks)
    img = strips[0]
    for stripidx in range(1, len(strips)):
        img = img.insert(strips[stripidx], 0, stripidx * _iterTileSize, expand=True)
    if img.bands > 3:
        img = img[:3]
    elif img.bands == 2:
        img = img[:1]
    return img


def redact_wsi_geojson(geojson, width, height, origImage):
    """
    Given an original image and a geojson record, produce a redacted image.

    :param geojson: geojson to redact.
    :param width: the width of the original image.
    :param height: the height of the original image.
    :param origImage: a vips image.
    :returns: redactedImage: a vips image.
    """
    polys = geojson_to_polygons(geojson)
    logger.info("Redacting wsi - polygons: %r", polys)
    svgImage = None
    chunk = 16384
    for yoffset in range(0, height, chunk):
        for xoffset in range(0, width, chunk):
            polygonSvg = polygons_to_svg(
                polys,
                min(width - xoffset, chunk),
                min(height - yoffset, chunk),
                cropAllowed=True,
                offsetx=xoffset,
                offsety=yoffset,
            )
            logger.info("Redacting wsi - svg: %r", polygonSvg)
            chunkImage = pyvips.Image.svgload_buffer(polygonSvg.encode())
            if not svgImage:
                svgImage = chunkImage
            else:
                svgImage = svgImage.insert(chunkImage, xoffset, yoffset, expand=True)
    logger.info("Redacting wsi - compositing")
    redactedImage = origImage.composite([svgImage], pyvips.BlendMode.OVER)
    if redactedImage.bands > 3:
        redactedImage = redactedImage[:3]
    elif redactedImage.bands == 2:
        redactedImage = redactedImage[:1]
    return redactedImage


def add_title_to_image(
    image, title, previouslyAdded=False, minWidth=384, background="#000000", textColor="#ffffff", square=True
):
    """
    Add a title to an image.  If the image doesn't exist, a new image is made
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
    :returns: a PIL image.
    """
    mode = "RGB"
    if image is None:
        image = PIL.Image.new(mode, (0, 0))
    image = image.convert(mode)
    w, h = image.size
    background = PIL.ImageColor.getcolor(background, mode)
    textColor = PIL.ImageColor.getcolor(textColor, mode)
    targetW = max(minWidth, w)
    fontSize = 0.15
    imageDraw = PIL.ImageDraw.Draw(image)
    for iter in range(3, 0, -1):
        try:
            imageDrawFont = PIL.ImageFont.truetype(
                font="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", size=int(fontSize * targetW)
            )
        except IOError:
            try:
                imageDrawFont = PIL.ImageFont.truetype(size=int(fontSize * targetW))
            except IOError:
                imageDrawFont = PIL.ImageFont.load_default()
        textW, textH = imageDraw.textsize(title, imageDrawFont)
        if iter != 1 and (textW > targetW * 0.95 or textW < targetW * 0.85):
            fontSize = fontSize * targetW * 0.9 / textW
    titleH = int(math.ceil(textH * 1.25))
    if square and (w != h or (not previouslyAdded or w != targetW or h < titleH)):
        if targetW < h + titleH:
            targetW = h + titleH
        else:
            titleH = targetW - h
    if previouslyAdded and w == targetW and h >= titleH:
        newImage = image.copy()
    else:
        newImage = PIL.Image.new(mode=mode, size=(targetW, h + titleH), color=background)
        newImage.paste(image, (int((targetW - w) / 2), titleH))
    imageDraw = PIL.ImageDraw.Draw(newImage)
    imageDraw.rectangle((0, 0, targetW, titleH), fill=background, outline=None, width=0)
    imageDraw.text(
        xy=(int((targetW - textW) / 2), int((titleH - textH) / 2)), text=title, fill=textColor, font=imageDrawFont
    )
    return newImage


def redact_topleft_square(image):
    """
    Replace the top left square of an image with black.

    :param image: a PIL image to adjust.
    :returns: an adjusted PIL image.
    """
    mode = "RGB"
    newImage = image.convert(mode)
    w, h = image.size
    background = PIL.ImageColor.getcolor("#000000", mode)
    imageDraw = PIL.ImageDraw.Draw(newImage)
    imageDraw.rectangle((0, 0, min(w, h), min(w, h)), fill=background, outline=None, width=0)
    return newImage


def refile_image(item, user, tokenId, imageId, uploadInfo=None):
    """
    Refile an item to a new name and folder.

    :param item: the girder item to move.
    :param user: the user authorizing the move.
    :param tokenId: the new folder name.
    :param imageId: the new item name without extension.
    :param uploadInfo: a dictionary of imageIds that contain additional fields.
        If it doesn't exist or the imageId is not present in it, it is not
        used.
    :returns: the modified girder item.
    """
    # if imageId starts with folder key, auto assign a number
    originalImageId = imageId
    if imageId.startswith(TokenOnlyPrefix):
        baseImageId = imageId[len(TokenOnlyPrefix) :]
        used = {
            int(entry["name"][len(baseImageId) + 1 :].split(".")[0])
            for entry in Item().find({"name": {"$regex": "^" + re.escape(baseImageId) + r"_[0-9]+\..*"}})
        }
        nextValue = 1
        while nextValue in used:
            nextValue += 1
        imageId = baseImageId + "_" + str(nextValue)
    ingestFolderId = Setting().get(PluginSettings.HUI_INGEST_FOLDER)
    ingestFolder = Folder().load(ingestFolderId, force=True, exc=True)
    parentFolder = Folder().findOne({"name": tokenId, "parentId": ingestFolder["_id"]})
    if not parentFolder:
        parentFolder = Folder().createFolder(ingestFolder, tokenId, creator=user)
    newImageName = f'{imageId}.{item["name"].split(".")[-1]}'
    originalName = item["name"]
    item["name"] = newImageName
    item = Item().move(item, parentFolder)
    redactList = get_standard_redactions(item, imageId)
    itemMetadata = {
        "redactList": redactList,
    }
    if uploadInfo and originalImageId in uploadInfo:
        itemMetadata["deidUpload"] = uploadInfo[originalImageId]["fields"]
    else:
        itemMetadata["deidUpload"] = {}
    itemMetadata["deidUpload"]["InputFileName"] = originalName
    item = Item().setMetadata(item, itemMetadata)
    if "wsi_uploadInfo" in item:
        del item["wsi_uploadInfo"]
        item = Item().save(item)
    return item
