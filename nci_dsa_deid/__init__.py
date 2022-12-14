from girder import plugin


class GirderPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'nci-dsa-deid'
    CLIENT_SOURCE_PATH = 'web_client'

    def load(self, info):
        print("Hello cruel world")
        # add plugin loading logic here
        pass
