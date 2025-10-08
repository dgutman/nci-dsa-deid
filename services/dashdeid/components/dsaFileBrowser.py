"""This is a panel to browse a DSA instance starting at the collection level """

import dash_bootstrap_components as dbc
from dash import html
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
import dash_mantine_components as dmc
import dash_ag_grid as dag

# from settings import gc
from girder_client import HttpError
import girder_client

from components.dsa_login_panel import getGc


SIDEBAR_COLLAPSED = {
    # "position": "fixed",
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
TOGGLE_BUTTON_STYLE = {
    "z-index": 2,  # This ensures the button is above other elements
}

VERTICAL_TEXT_STYLE = {
    "top": "50%",
    "left": "10px",
    "transform": "translateY(-50%) rotate(-90deg)",
    "z-index": 1,  # Below the toggle button but above other elements
    "white-space": "nowrap",
    "font-weight": "bold",
}
## If level=1 it means it's a root folder for a collection


CONTENT_STYLE = {
    "transition": "margin-left .5s",
    "margin-left": "-1rem",  # Adjusted from 32rem
    "margin-right": "2rem",
    "padding": "0rem 0rem",
    "background-color": "#f8f9fa",
    "width": "580px",
}


def folder_div(collection_folder, folder_cache):
    if collection_folder["_modelType"] == "collection":
        level = 1
    else:
        level = 2

    ## update the folder cache
    folder_cache[collection_folder["_id"]] = collection_folder["name"]

    return html.Div(
        [
            dmc.Button(
                collection_folder["name"],
                leftIcon=DashIconify(icon="material-symbols:folder", width=20),
                id={"type": "folder", "id": collection_folder["_id"], "level": level},
                n_clicks=0,
                variant="subtle",
                style={
                    "text-align": "left",
                    "margin-left": f"{20*level-25}px",
                    "padding": "2px 8px",
                    "font-size": "1rem",
                    "height": "20px",
                },
            ),
            html.Div(
                id={
                    "type": "subfolders",
                    "id": collection_folder["_id"],
                    "level": level,
                },
                style={"margin-left": f"{20*(level)-10}px"},
            ),
        ],
        style={
            "margin-top": "-4px",
            "margin-bottom": "-4px",
        },  # Adjust these values as needed
    )


def get_tree_components():
    """Get the tree components for the collections."""
    try:
        tree_components = [
            dcc.Markdown(
                "## Folder Tree",
                style={"marginBottom": 10, "marginTop": 10, "marginLeft": 10},
            )
        ]

        collections = getGc().get("collection")

        # Create a global dictionary for the cache
        ### May want to refactor this... not sure this is the best way to do this
        folder_cache = {}

        ## Preseed this with collection names
        for c in collections:
            folder_cache[c["_id"]] = c["name"]

        for collection in collections:
            tree_components.append(folder_div(collection, folder_cache))

        return tree_components, folder_cache
    except:
        return [
            dcc.Markdown(
                "## ",
                style={"marginBottom": 10, "marginTop": 10, "marginLeft": 10},
            )
        ], None


tree_components, folder_cache = get_tree_components()


@callback(
    Output("fld-tree-collapse", "children"),
    Input("metadata_store", "data"),
    Input("login-state", "data"),
)
def update_tree_components(metadata, loginState):
    global folder_cache
    tree_components, folder_cache = get_tree_components()
    return tree_components


tree_layout = html.Div(
    [
        dbc.Collapse(
            [html.Div("")],
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
    style={
        "display": "flex",
        "background-color": "#f8f9fa",
        "height": "100%",
        "overflow-y": "scroll",
    },
)


record_match_status = html.Div(id="file-match-info", style={"margin-left": "50px"})


content = dbc.Row(
    [
        dbc.Col(
            [
                html.Div(
                    id="itemListinfo",
                    children=[
                        dag.AgGrid(
                            id="itemGrid",
                            columnSize="autoSize",
                            dashGridOptions={
                                "pagination": True,
                                "paginationAutoPageSize": True,
                            },
                            columnDefs=[
                                {"field": "name", "headerName": "Filename"},
                                {
                                    "field": "size",
                                    "headerName": "File Size",
                                    "width": 150,
                                    "columnSize": "autoSize",
                                },
                                {"field": "_id", "headerName": "DSA ID"},
                                {
                                    "field": "match_result",
                                    "headerName": "Matching Metadata",
                                },
                            ],
                            defaultColDef={
                                "resizable": True,
                                "sortable": True,
                                "filter": True,
                                "flex": 1,
                                "cellStyle": {
                                    "styleConditions": [
                                        {
                                            "condition": "params.value == 'No Match'",
                                            "style": {
                                                "fontWeight": "bold",
                                                "color": "red",
                                            },
                                        },
                                        {
                                            "condition": "params.value == 'Matched'",
                                            "style": {
                                                "fontWeight": "bold",
                                                "color": "green",
                                            },
                                        },
                                    ]
                                },
                            },
                        ),
                    ],
                    style=CONTENT_STYLE,
                )
            ],
            width=8,
        ),
        dbc.Col([record_match_status], width=3),
    ]
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
            [html.Div(sidebar, style={"marginRight": 15}), content],
            style={"display": "flex"},
        ),
    ],
    style={"height": "100%"},
)


slideListTab_content = html.Div(
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


### This populates some stats on the number of items in the metadata CSV file, the current item set, and the number of matches


@callback(
    Output("file-match-info", "children"),
    Input("metadata_store", "data"),
    Input("itemList_store", "data"),
)
def update_file_match_info(metadata, itemList):
    if metadata and itemList:
        metadataCount = len(metadata)
        itemCount = len(itemList)
        matchedCount = len([i for i in itemList if i["match_result"] == "Matched"])
        return html.Div(
            [
                html.H5(
                    f"Metadata Items: {metadataCount}", className="alert alert-primary"
                ),
                html.H5(
                    f"Item List Items: {itemCount}", className="alert alert-success"
                ),
                html.H5(f"Matched Items: {matchedCount}", className="alert alert-info"),
            ],
            className="my-3",
        )
    return html.Div(
        [html.H5("No Metadata or Item List Data", className="alert alert-danger")],
        className="my-3",
    )


### CALLBACKS
@callback(
    [
        Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "style"),
        Output(
            {"type": "folder", "id": MATCH, "level": MATCH}, "children"
        ),  # Add this line for the button's label
    ],
    [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
    [
        State({"type": "folder", "id": MATCH, "level": MATCH}, "id"),
        State("last_clicked_folder", "data"),
    ],
    prevent_initial_call=True,
)
def update_folder_styles_and_icons(n_clicks, folder_id, last_clicked_folder_data):
    children = []
    icon = DashIconify(icon="material-symbols:folder", width=20)
    style = {"color": "blue"}
    button_label = folder_cache[folder_id["id"]]  # None  # Initialize the button label

    if n_clicks % 2 == 1:  # folder was expanded
        level = folder_id["level"]
        # Fetch item count for the clicked folder

        itemList = []
        folderName = folder_cache[folder_id["id"]]
        ## This will fail for root folders as they can't contain items..
        try:
            itemList = list(gc.listItem(folder_id["id"]))
        except:
            itemList = []
        itemCount = len(itemList) if itemList else 0
        button_label = f"{folderName} ({itemCount})"  # Modify the button's label to include the count

        if level == 1:
            subfolders = getGc().get(
                "folder?parentType=collection&parentId=%s" % folder_id["id"]
            )
        else:
            subfolders = getGc().get(
                "folder?parentType=folder&parentId=%s" % folder_id["id"]
            )
            itemList = getGc().get(f"item?folderId={folder_id['id']}")

        if subfolders:
            children = [
                html.Div(folder_div(subfolder, folder_cache))
                for subfolder in subfolders
            ]
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
    return []


@callback(
    [Output("last_clicked_folder", "data")],
    [Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks")],
    [State({"type": "folder", "id": ALL, "level": ALL}, "id")],
    prevent_initial_call=True,
)
def update_last_clicked_folder(n_clicks, folder_ids):
    # Extract the folder ID from the callback context to find which folder was clicked
    ctx = callback_context

    try:
        triggered_id = json.loads(
            callback_context.triggered[0]["prop_id"].split(".")[0]
        )
        return (triggered_id,)
    except json.JSONDecodeError:

        return (no_update,)  # or some other appropriate default value or behavior


## LOGIC BUG HERE IF FOLDER HAS A SUBFOLDER HAS A SUBFOLDER..
@callback(
    Output("itemList_store", "data"),
    [Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks")],
    [State({"type": "folder", "id": ALL, "level": ALL}, "id")],
    Input("metadata_store", "data"),
    prevent_initial_call=True,
)
def update_recently_clicked_folder(n_clicks, folder_id, metadata):
    filesWithMetadata = []
    if metadata:
        filesWithMetadata = [row["InputFileName"] for row in metadata]

    trigger = callback_context.triggered[0]
    prop_id_string = trigger["prop_id"].rsplit(".", 1)[0]
    try:
        prop_id_dict = json.loads(prop_id_string)
    except json.JSONDecodeError:
        # print(
        #     f"update_recently_flicked_folder Failed.. DEBUG! Failed to parse JSON from: {prop_id_string}"
        # )
        return no_update  # or some other appropriate default value or behavior

    # Now you can extract the desired values from the dictionary
    level = prop_id_dict["level"]
    folder_type = prop_id_dict["type"]
    folder_id = prop_id_dict["id"]

    ## This logic may not always work ... if the folder has subfolders
    if level == 2 and trigger["value"] > 0:
        itemListInfoData = list(getGc().listItem(folder_id))

        for i in itemListInfoData:
            if i["name"] in filesWithMetadata:
                i["match_result"] = "Matched"
            else:
                i["match_result"] = "No Match"

        return itemListInfoData

    return no_update  ### if there's an error?


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
