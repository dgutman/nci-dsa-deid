import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash import html, dcc, Input, Output, callback

import settings as s
from components.dsa_login_panel import getGc


def _determine_status_from_path(path: str) -> str:
    if not path:
        return "Unknown"
    if path.startswith("/collection/WSI DeID/Approved"):
        return "In Approved Status"
    if path.startswith("/collection/WSI DeID/Redacted"):
        return "In Redacted Folder"
    if path.startswith("/collection/WSI DeID/AvailableToProcess"):
        return "AvailableToProcess Folder"
    if path.startswith("/collection/WSI DeID/Unfiled"):
        return "Unfiled"
    return "Other"


collection_overview_panel = html.Div(
    [
        html.Div(
            [
                dbc.Button(
                    "Refresh Collection Items",
                    id="refresh-collection-items",
                    color="secondary",
                    n_clicks=0,
                ),
                html.Span(
                    " Listing all items under DEID collection.",
                    style={"marginLeft": "10px"},
                ),
            ]
        ),
        dcc.Store(id="collection-items-store"),
        html.Div(id="collection-items-grid"),
    ]
)


@callback(
    Output("collection-items-store", "data"),
    Input("refresh-collection-items", "n_clicks"),
    prevent_initial_call=False,
)
def load_collection_items(n_clicks):
    try:
        items = getGc().get(
            f"resource/{s.DEID_COLLECTION_ID}/items?type=collection&limit=0"
        )
    except Exception:
        items = []

    rows = []
    for it in items:
        try:
            path = getGc().get(f"resource/{it['_id']}/path?type=item")
        except Exception:
            path = None
        rows.append(
            {
                "_id": it.get("_id"),
                "name": it.get("name"),
                "path": path,
                "size": it.get("size", 0),
                "status": _determine_status_from_path(path or ""),
            }
        )
    return rows


@callback(Output("collection-items-grid", "children"), Input("collection-items-store", "data"))
def render_collection_items_grid(data):
    if not data:
        return html.Div("No items found in collection.")
    column_defs = [
        {"field": "status", "width": 200, "editable": False},
        {"field": "name", "width": 320, "editable": False},
        {"field": "path", "width": 600, "editable": False},
        {"field": "size", "width": 140, "editable": False},
    ]
    return dag.AgGrid(
        id="collection-items-aggrid",
        rowData=data,
        columnDefs=column_defs,
        defaultColDef=dict(resizable=True, sortable=True),
        dashGridOptions={"rowHeight": 22, "rowSelection": "single"},
    )



