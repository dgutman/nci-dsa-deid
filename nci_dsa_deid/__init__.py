from girder import plugin
import wsi_deid.process
from pylibdmtx.pylibdmtx import encode
from . import nciProcess


class GirderPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = "nci-dsa-deid"
    CLIENT_SOURCE_PATH = "web_client"

    def load(self, info):
        print("Hello from the NCI DSA DEID Plugin")
        plugin.getPlugin("wsi_deid").load(info)

        oldFunc = wsi_deid.process.add_title_to_image

        wsi_deid.process.add_title_to_image = nciProcess.add_barcode_to_image
        # add plugin loading logic here


def genDataMatrixLabel():
    pass
