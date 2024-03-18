"""This is a panel to browse a DSA instance starting at the collection level """

import dash_bootstrap_components as dbc
from dash import html
import girder_client
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
import girder_client, json
import dash_mantine_components as dmc
import settings as s
import dash_ag_grid as dag
import dash

# # Replace with the base URL of  the DSA
# gc = girder_client.GirderClient(apiUrl=s.DSA_BASE_URL)
from settings import gc

collections = gc.get("collection")

# Create a global dictionary for the cache
folder_cache = {}

## Preseed this with collection names

for c in collections:
    folder_cache[c["_id"]] = c["name"]
    # print(c["name"])

# ## To simplify the logic, I am going to pre-Cache the collection Name as well as the
# ## First set of subfolders, as they require a different girder call to the getFolder
# ## call and it becomes confusing to follow..


SIDEBAR_COLLAPSED = {
    # "position": "fixed",
    "top": 62.5,
    "left": "-27rem",  # Adjust this value so a portion of the sidebar remains visible
    "bottom": 0,
    # "width": "30rem",  # Keep the width the same as the expanded sidebar
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0rem 0rem",
    "background-color": "#f8f9fa",
}
# Define the new style for the toggle button and the vertical text
TOGGLE_BUTTON_STYLE = {
    # # "position": "relative",
    # "top": "155px",
    # "left": "35px",
    # "width": 50,
    # "padding-right": -20,
    "z-index": 2,  # This ensures the button is above other elements
}

VERTICAL_TEXT_STYLE = {
    # "position": "absolute",
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
    "width": "100%",
}


def get_folder_name(folder_id, level=2):
    """
    Get the folder name for a given folder_id.
    If the folder_id is not in the cache, fetch it using girder_client.
    """
    # Check if folder_id is in the cache
    if folder_id in folder_cache:
        return folder_cache[folder_id]

    # If not in cache, fetch using girder_client
    try:
        folder_info = gc.getFolder(folder_id)
        folder_name = folder_info["name"]
        # Update the cache
        folder_cache[folder_id] = folder_name
        return folder_name
    except:
        print(f"Failed to fetch folder name for id: {folder_id}")
        return None


def folder_div(collection_folder):
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


tree_components = [
    dcc.Markdown(
        "## Folder Tree", style={"marginBottom": 10, "marginTop": 10, "marginLeft": 10}
    )
]

for collection in collections:
    tree_components.append(folder_div(collection))

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
    # print(n_clicks, folder_id)
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

    #  style={
    #                     "text-align": "left",
    #                     "margin-left": f"{20*level-25}px",
    #                     "padding": "2px 8px",
    #                     "font-size": "1rem",
    #                     "height": "20px",
    #                 },

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
    ctx = callback_context
    print("Context was", ctx.triggered_id)

    try:
        triggered_id = json.loads(
            callback_context.triggered[0]["prop_id"].split(".")[0]
        )
        return (triggered_id,)
    except json.JSONDecodeError:

        print(
            f"In dfb update_last_clicked Failed to parse JSON from: {callback_context.triggered[0]['prop_id'].split('.')[0]}"
        )
        return (no_update,)  # or some other appropriate default value or behavior
    return no_update


## LOGIC BUG HERE IF FOLDER HAS A SUBFOLDER HAS A SUBFOLDER..
@callback(
    Output("itemList_store", "data"),
    [Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks")],
    [State({"type": "folder", "id": ALL, "level": ALL}, "id")],
    prevent_initial_call=True,
)
def update_recently_clicked_folder(n_clicks, folder_id):
    print(folder_id, "triggered this callback this time")
    print(n_clicks, "are the n_clicks data")

    trigger = callback_context.triggered[0]
    print(folder_id, n_clicks, trigger)
    print(trigger, "is the triger...")
    prop_id_string = trigger["prop_id"].rsplit(".", 1)[0]
    try:
        prop_id_dict = json.loads(prop_id_string)
    except json.JSONDecodeError:
        print(
            f"update_recently_flicked_folder Failed.. DEBUG! Failed to parse JSON from: {prop_id_string}"
        )
        return no_update  # or some other appropriate default value or behavior

    # Now you can extract the desired values from the dictionary
    level = prop_id_dict["level"]
    folder_type = prop_id_dict["type"]
    folder_id = prop_id_dict["id"]
    # print(level, folder_type, folder_id)

    ## This logic may not always work ... if the folder has subfolders
    if level == 2 and trigger["value"] > 0:
        itemListInfoData = list(gc.listItem(folder_id))
        # print(itemListInfo)
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
