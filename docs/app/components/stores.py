# Put all the dash.dcc.Stores here.
from dash import html, dcc

stores = html.Div(
    [
        dcc.Store(id="user-store", storage_type="local", data={}),
        dcc.Store(id="itemList_store", data=[]),
        dcc.Store(id="metadata_store", data=[]),
        dcc.Store(id="mergedItem_store", data=[]),
        dcc.Store({"type": "datastore", "id": "ils", "level": 2}, data=[]),
        dcc.Store(id="submit-button-state-store", data={"disabled": False}),
    ]
)
