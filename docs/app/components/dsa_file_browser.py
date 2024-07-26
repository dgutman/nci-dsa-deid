"""This is a panel to browse a DSA instance starting at the collection level """

import dash_bootstrap_components as dbc
from dash import html
from girder_client import GirderClient
from dash import (
    dcc,
    html,
    Input,
    Output,
    State,
    callback_context,
    MATCH,
    ALL,
    callback,
    no_update,
)
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import json
import settings as s
import dash_ag_grid as dag
from concurrent.futures import ThreadPoolExecutor
from os import getenv

from utils.utils import folder_div, process_row

SIDEBAR_COLLAPSED = {
    "top": 62.5,
    "left": "-27rem",  # Adjust this value so a portion of the sidebar remains visible
    "bottom": 0,
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0rem 0rem",
    "background-color": "#f8f9fa",
}

# Define the new style for the toggle button and the vertical text
TOGGLE_BUTTON_STYLE = {"z-index": 2}

VERTICAL_TEXT_STYLE = {
    "top": "50%",
    "left": "10px",
    "transform": "translateY(-50%) rotate(-90deg)",
    "z-index": 1,  # Below the toggle button but above other elements
    "white-space": "nowrap",
    "font-weight": "bold",
}

CONTENT_STYLE = {
    "transition": "margin-left .5s",
    "margin-left": "-1rem",  # Adjusted from 32rem
    "margin-right": "2rem",
    "padding": "0rem 0rem",
    "background-color": "#f8f9fa",
    "width": "100%",
}

tree_components = [
    dcc.Markdown(
        "## Folder Tree", style={"marginBottom": 10, "marginTop": 10, "marginLeft": 10}
    ),
    html.Div(id="folder-tree"),
]

tree_layout = html.Div(
    [
        dbc.Collapse(
            tree_components,
            is_open=True,
            id="fld-tree-collapse",
            dimension="width",
        ),
        dbc.Button(
            DashIconify(icon="bi:arrow-left-circle-fill"),
            id="btn_sidebar",
            className="toggle-button",
            style=TOGGLE_BUTTON_STYLE,
        ),
    ],
    style={"display": "flex", "background-color": "#f8f9fa", "height": "100%"},
)


content = html.Div(
    id="itemListinfo",
    children=[
        dag.AgGrid(
            id="itemGrid",
            columnSize="autoSize",
            dashGridOptions={"pagination": True, "paginationAutoPageSize": True},
            columnDefs=[
                {"field": "name", "headerName": "Filename"},
                {
                    "field": "size",
                    "headerName": "File Size",
                    "width": 150,
                    "columnSize": "autoSize",
                },
                {"field": "_id", "headerName": "DSA ID"},
                {"field": "match_result", "headerName": "Matching Metadata"},
            ],
            defaultColDef={
                "resizable": True,
                "sortable": True,
                "filter": True,
                "flex": 1,
            },
        )
    ],
    style=CONTENT_STYLE,
)


sidebar = html.Div(
    [
        dcc.Store(id="last_clicked_folder"),
        dcc.Store(id="folderId_store"),
        tree_layout,
    ],
    id="sidebar",
    style={
        "border": "4px solid #ddd",  # Optional: adds a border around the div
        "margin": "1px",  # Adjust the margin here
        "padding": "1px",
        "box-shadow": "none",  # Adjust the padding here
        "height": "100%",
        "background-color": "#f8f9fa",
    },
)


dsaFileTree_layout = html.Div(
    [
        dcc.Store(id="side_click"),
        dcc.Location(id="url"),
        html.Div(
            [
                html.Div(sidebar, style={"marginRight": 15}),
                content,
            ],
            style={"display": "flex"},
        ),
    ],
    style={"height": "100%"},
)


dsa_file_browser = html.Div(
    [
        dbc.Row(
            [
                dbc.Row(
                    [
                        dbc.Button(
                            "Match Metadata",
                            id="check-match-button",
                            className="me-2",
                            style={"maxWidth": 300},
                        ),
                        dbc.Button(
                            "JustDeID",
                            id="no-meta-deid-button",
                            className="me-1",
                            style={"maxWidth": 300},
                        ),
                        html.Div(id="current_selected_folder"),
                    ]
                ),
            ],
            className="mt-4",
        ),
        dsaFileTree_layout,
    ],
    style={"height": "100%"},
)


# Callbacks
@callback(
    [Output("fld-tree-collapse", "is_open"), Output("btn_sidebar", "children")],
    [
        Input("btn_sidebar", "n_clicks"),
        State("fld-tree-collapse", "is_open"),
    ],
    prevent_initial_call=True,
)
def collapse_tree(n_clicks: int, is_open) -> bool:
    if n_clicks:
        if is_open:
            return False, DashIconify(icon="bi:arrow-right-circle-fill")
        else:
            return True, DashIconify(icon="bi:arrow-left-circle-fill")

    return no_update, no_update


@callback(
    Output("folder-tree", "children"),
    [Input("folder-tree", "id"), Input("user-store", "data")],
)
def update_folder_tree(_, user_data):
    token = user_data.get("token")

    gc = GirderClient(apiUrl=getenv("DSA_API_URL"))

    if token is not None:
        gc.token = token

    collections = gc.listCollection()

    return [folder_div(c) for c in collections]


@callback(
    [
        Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "style"),
        Output(
            {"type": "folder", "id": MATCH, "level": MATCH}, "children"
        ),  # Add this line for the button's label
    ],
    [
        Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks"),
        State({"type": "folder", "id": MATCH, "level": MATCH}, "id"),
        State("last_clicked_folder", "data"),
        State("user-store", "data"),
    ],
    prevent_initial_call=True,
)
def update_folder_styles_and_icons(
    n_clicks, folder_id, last_clicked_folder_data, user_data
):
    gc = GirderClient(apiUrl=getenv("DSA_API_URL"))
    token = user_data.get("token")

    if token is not None:
        gc.token = token

    children = []
    icon = DashIconify(icon="material-symbols:folder", width=20)
    style = {"color": "blue"}

    try:
        name = gc.getFolder(folder_id["id"])["name"]
    except:
        name = gc.getCollection(folder_id["id"])["name"]

    button_label = name

    if n_clicks % 2 == 1:  # folder was expanded
        level = folder_id["level"]
        # Fetch item count for the clicked folder

        itemList = []

        folderName = name
        ## This will fail for root folders as they can't contain items..
        try:
            itemList = list(gc.listItem(folder_id["id"]))
        except:
            itemList = []
        itemCount = len(itemList) if itemList else 0
        button_label = f"{folderName} ({itemCount})"  # Modify the button's label to include the count

        if level == 1:
            subfolders = gc.get(
                "folder?parentType=collection&parentId=%s" % folder_id["id"]
            )
        else:
            subfolders = gc.get(
                "folder?parentType=folder&parentId=%s" % folder_id["id"]
            )
            itemList = gc.get(f"item?folderId={folder_id['id']}")

        if subfolders:
            children = [html.Div(folder_div(subfolder)) for subfolder in subfolders]
            icon = DashIconify(icon="material-symbols:folder-open-rounded", width=20)
            style = {"color": "green"}
        else:
            icon = DashIconify(icon="material-symbols:folder", width=20)

    # Additional logic to handle style change:
    last_clicked_id = last_clicked_folder_data if last_clicked_folder_data else None
    if last_clicked_id == folder_id["id"]:
        style = {
            "color": "green",
            "font-size": "1rem",
            "height": "20px",
            "padding": "2px 8px",
        }
    elif last_clicked_id:
        style = {
            "color": "blue",
            "font-size": "1rem",
            "height": "20px",
            "padding": "2px 8px",
        }
    else:
        style = {
            "color": "blue",
            "font-size": "1rem",
            "height": "20px",
            "padding": "2px 8px",
        }

    return children, icon, style, button_label


@callback(Output("itemGrid", "rowData"), [Input("itemList_store", "data")])
def dumpItemList(itemList):
    if itemList:
        return itemList
        ## Make this into a datatable...
    return []


@callback(
    [Output("last_clicked_folder", "data")],
    [Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks")],
    [State({"type": "folder", "id": ALL, "level": ALL}, "id")],
    prevent_initial_call=True,
)
def update_last_clicked_folder(n_clicks, folder_ids):
    # Extract the folder ID from the callback context to find which folder was clicked
    try:
        triggered_id = json.loads(
            callback_context.triggered[0]["prop_id"].split(".")[0]
        )
        return (triggered_id,)
    except json.JSONDecodeError:
        return (no_update,)  # or some other appropriate default value or behavior


@callback(
    Output("itemList_store", "data"),
    [
        Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks"),
        State({"type": "folder", "id": ALL, "level": ALL}, "id"),
        State("user-store", "data"),
    ],
    prevent_initial_call=True,
)
def update_recently_clicked_folder(_, folder_id, user_data):
    token = user_data.get("token")

    gc = GirderClient(apiUrl=getenv("DSA_API_URL"))

    if token is not None:
        gc.token = token

    trigger = callback_context.triggered[0]

    prop_id_string = trigger["prop_id"].rsplit(".", 1)[0]

    try:
        prop_id_dict = json.loads(prop_id_string)
    except json.JSONDecodeError:
        return no_update  # or some other appropriate default value or behavior

    # Now you can extract the desired values from the dictionary
    level = prop_id_dict["level"]
    folder_type = prop_id_dict["type"]
    folder_id = prop_id_dict["id"]

    # This logic may not always work ... if the folder has subfolders
    if level == 2 and trigger["value"] > 0:
        itemListInfoData = list(gc.listItem(folder_id))

        return itemListInfoData

    return no_update


@callback(
    [
        Output("mergedItem_store", "data"),
        Output("main-tabs", "active_tab"),  # Add this line
    ],
    [
        Input("check-match-button", "n_clicks"),
        State("metadata_store", "data"),
        State("itemList_store", "data"),
        State("user-store", "data"),
    ],
    prevent_initial_call=True,
)
def check_name_matches(_, metadata, itemlist_data, user_data):
    if len(user_data):
        gc = GirderClient(apiUrl=getenv("DSA_API_URL"))
        gc.token = user_data.get("token")
    else:
        return no_update, no_update

    ctx = callback_context

    s.logger.info(f"{len(metadata)} rows are in the metadata table")
    s.logger.info(f"{len(itemlist_data)} rows are in the current itemlist")

    if metadata:
        metadata_mapping = {row["InputFileName"]: row for row in metadata}
    else:
        metadata_mapping = {}

    with ThreadPoolExecutor() as executor:
        results = list(
            executor.map(
                process_row,
                gc,
                itemlist_data,
                [s.COLS_FOR_COPY] * len(itemlist_data),
                [metadata_mapping]
                * len(itemlist_data),  ## Note this oddity of science..
            )
        )

    if ctx.triggered_id == "validate-deid-status-button":
        return results, "merged-data"
    else:
        return results, "merged-data"
