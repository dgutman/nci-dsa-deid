import pytest

from girder.plugin import loadedPlugins


@pytest.mark.plugin('nci_dsa_deid')
def test_import(server):
    assert 'nci_dsa_deid' in loadedPlugins()
