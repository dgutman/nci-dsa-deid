"""This is a panel to browse a DSA instance starting at the collection level """
import dash_bootstrap_components as dbc
from dash import html
import girder_client
from dash import dcc, html, Input, Output, State, callback_context, MATCH, ALL, callback
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


SIDEBAR_STYLE = {
    "position": "relative",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "30rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0.5rem 1rem",
    "background-color": "#f8f9fa",
}


SIDEBAR_COLLAPSED = {
    # "position": "fixed",
    "top": 62.5,
    "left": "-27rem",  # Adjust this value so a portion of the sidebar remains visible
    "bottom": 0,
    "width": "30rem",  # Keep the width the same as the expanded sidebar
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


tree_layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    dcc.Markdown("## Folder Tree"), width=11
                ),  # This takes up 11 out of 12 parts of the width
                dbc.Col(
                    dbc.Button(
                        DashIconify(icon="bi:arrow-left-circle-fill"),
                        id="btn_sidebar",
                        className="toggle-button",
                        style=TOGGLE_BUTTON_STYLE,
                        n_clicks=0,
                    ),
                    width=1,  # This takes up 1 out of 12 parts of the width
                    style={"padding": 0, "margin-left": "-10px", "margin-top": "10px"},
                ),
            ]
        ),
        html.Div(
            [
                html.Div(
                    folder_div(collection),
                )
                for collection in collections
            ],
            style={
                "height": "750px",
                "overflow": "scroll",
                "border": "0px",
                "padding-right": "0px",
                "border": "0px",
            },
        ),
    ],
    style={
        "border": "4px solid #ddd",  # Optional: adds a border around the div
        "margin": "1px",  # Adjust the margin here
        "padding": "1px",
        "box-shadow": "none",  # Adjust the padding here
    },
)


sidebar = html.Div(
    [
        dcc.Store(id="last_clicked_folder"),
        dcc.Store(id="folderId_store"),
        tree_layout,
    ],
    id="sidebar",
    style=SIDEBAR_STYLE,
)

content = html.Div(id="itemListinfo", style=CONTENT_STYLE)

dsaFileTree_layout = dbc.Row(
    [
        dcc.Store(id="side_click"),
        dcc.Location(id="url"),
        dbc.Col(sidebar, width=3, style={"padding": 0}, id="sidebar_col"),
        dbc.Col(content, width=9, id="content_col"),
    ],
)


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


@callback(Output("itemListinfo", "children"), [Input("itemList_store", "data")])
def dumpItemList(itemList):
    if itemList:
        ## Make this into a datatable...
        itemTable = dag.AgGrid(
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
            rowData=itemList,
            defaultColDef={
                "resizable": True,
                "sortable": True,
                "filter": True,
                "flex": 1,
            },
        )
        return itemTable


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
    except json.JSONDecodeError:
        print(
            f"Failed to parse JSON from: {callback_context.triggered[0]['prop_id'].split('.')[0]}"
        )
        return ("",)  # or some other appropriate default value or behavior

    return (triggered_id,)


@callback(
    Output("itemList_store", "data"),
    [Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks")],
    [State({"type": "folder", "id": ALL, "level": ALL}, "id")],
    prevent_initial_call=True,
)
def update_recently_clicked_folder(folder_id, n_clicks):
    # print(folder_id, n_clicks)
    trigger = callback_context.triggered[0]

    prop_id_string = trigger["prop_id"].rsplit(".", 1)[0]
    try:
        prop_id_dict = json.loads(prop_id_string)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from: {prop_id_string}")
        return {}  # or some other appropriate default value or behavior

    # Now you can extract the desired values from the dictionary
    level = prop_id_dict["level"]
    folder_type = prop_id_dict["type"]
    folder_id = prop_id_dict["id"]
    # print(level, folder_type, folder_id)

    if level == 2:
        itemListInfoData = list(gc.listItem(folder_id))
        # print(itemListInfo)
        return itemListInfoData

    return {}


@callback(
    Output("sidebar", "style"),
    [Input("btn_sidebar", "n_clicks")],
    [State("sidebar", "style")],
    prevent_initial_call=True,
)
def toggle_sidebar(n, style):
    if style and "left" in style and style["left"] == "0px":
        return {**style, "left": "-25rem"}
    return {**style, "left": "0px"}


slideListTab_content = dbc.Row(
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
        dsaFileTree_layout,
    ],
    className="mt-4",
)

# # Add a callback to handle the collapsing and expanding of the sidebar
# @callback(
#     [
#         Output("sidebar_col", "style"),
#         Output("content_col", "style"),
#         Output("vertical_text", "style"),
#     ],
#     [Input("btn_sidebar", "n_clicks")],
#     prevent_initial_call=True,
# )
# def toggle_sidebar(n_clicks):
#     if n_clicks % 2 == 0:  # Sidebar is expanded
#         sidebar_style = {"padding": 0}
#         content_style = {"width": 9}
#         vertical_text_style = {"display": "none"}  # hide the vertical text
#     else:  # Sidebar is collapsed
#         sidebar_style = {"padding": 0, "width": 0}  # hide the sidebar
#         content_style = {"width": 10}  # expand the content
#         vertical_text_style = {"display": "block"}  # show the vertical text

#     return sidebar_style, content_style, vertical_text_style
