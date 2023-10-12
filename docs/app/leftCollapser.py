from dash import dcc, html, Input, Output, State, callback_context, MATCH, ALL, callback
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import girder_client, json
import dash_mantine_components as dmc
import settings as s
import dash_ag_grid as dag
import dash

# # Replace with the base URL of  the DSA
gc = girder_client.GirderClient(apiUrl=s.DSA_BASE_URL)
collections = gc.get("collection")


# Create a global dictionary for the cache
folder_cache = {}

## Preseed this with collection names

for c in collections:
    folder_cache[c["_id"]] = c["name"]

print(folder_cache)
## To simplify the logic, I am going to pre-Cache the collection Name as well as the
## First set of subfolders, as they require a different girder call to the getFolder
## call and it becomes confusing to follow..


# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 62.5,
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
    "position": "fixed",
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
    # "position": "absolute",
    "top": "15px",
    "left": "-20px",
    "width": 50,
    "z-index": 2,  # This ensures the button is above other elements
}

VERTICAL_TEXT_STYLE = {
    "position": "absolute",
    "top": "50%",
    "left": "10px",
    "transform": "translateY(-50%) rotate(-90deg)",
    "z-index": 1,  # Below the toggle button but above other elements
    "white-space": "nowrap",
    "font-weight": "bold",
}
## If level=1 it means it's a root folder for a collection


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
                    dcc.Markdown("## Folder Tree"), width=10
                ),  # This takes up 11 out of 12 parts of the width
                dbc.Col(
                    dbc.Button(
                        DashIconify(icon="bi:arrow-left-circle-fill"),
                        id="btn_sidebar",
                        className="toggle-button",
                        style=TOGGLE_BUTTON_STYLE,
                        n_clicks=0,
                    ),
                    width=2,  # This takes up 1 out of 12 parts of the width
                    style={"padding": 0, "margin-left": "-20px", "margin-top": "10px"},
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
        "margin": "-10px",  # Adjust the margin here
        "padding": "-10px",  # Adjust the padding here
    },
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

    if n_clicks % 2 == 1:  # folder was expanded
        level = folder_id["level"]
        # Fetch item count for the clicked folder

        itemList = []
        # try:
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

    # Additional logic to handle style change:
    last_clicked_id = last_clicked_folder_data if last_clicked_folder_data else None
    if last_clicked_id == folder_id["id"]:
        style = {"color": "blue"}
    elif last_clicked_id:
        style = {"color": "blue"}
    else:
        style = {"color": "green"}

    return children, icon, style, button_label


@callback(Output("itemListinfo", "children"), [Input("itemList_store", "data")])
def dumpItemList(itemList):
    if itemList:
        ## Make this into a datatable...
        itemTable = dag.AgGrid(
            id="itemGrid",
            columnSize="autoSize",
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
                # "columnSize": "autoSize",
            },
        )
        return itemTable
        # return html.Div(json.dumps(itemList, indent=2))


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
        return ({},)  # or some other appropriate default value or behavior

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
    # print(trigger["prop_id"])

    prop_id_string = trigger["prop_id"].rsplit(".", 1)[0]
    try:
        prop_id_dict = json.loads(prop_id_string)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON from: {prop_id_string}")
        return {}  # or some other appropriate default value or behavior

    # prop_id_dict = json.loads(trigger["prop_id"].split(".")[0])

    # Now you can extract the desired values from the dictionary
    level = prop_id_dict["level"]
    folder_type = prop_id_dict["type"]
    folder_id = prop_id_dict["id"]
    # print(level, folder_type, folder_id)

    if level == 2:
        itemListInfo = list(gc.listItem(folder_id))
        # print(itemListInfo)
        return itemListInfo

    return {}


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

navbar = dbc.NavbarSimple(
    children=[
        # dbc.Button(
        #     "Sidebar",
        #     outline=True,
        #     color="secondary",
        #     className="mr-1",
        #     id="btn_sidebar",
        # ),
        dbc.NavItem(dbc.NavLink("Page 1", href="#")),
    ],
    brand="NCI DSA DeID",
    brand_href="#",
    color="dark",
    dark=True,
    fluid=True,
)


# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "transition": "margin-left .5s",
    "margin-left": "32rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE1 = {
    "transition": "margin-left .5s",
    "margin-left": "2rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

sidebar = html.Div(
    [
        dcc.Store("itemList_store"),
        dcc.Store(id="last_clicked_folder"),
        dcc.Store(id="folderId_store"),
        # html.H2("DSA Folder Browser", className="display-6"),
        tree_layout,
    ],
    id="sidebar",
    style=SIDEBAR_STYLE,
)

content = html.Div(id="itemListinfo", style=CONTENT_STYLE)

app.layout = html.Div(
    [
        dcc.Store(id="side_click"),
        dcc.Location(id="url"),
        navbar,
        sidebar,
        content,
    ],
)


@app.callback(
    [
        Output("sidebar", "style"),
        Output("itemListinfo", "style"),
        Output("side_click", "data"),
    ],
    [Input("btn_sidebar", "n_clicks")],
    [
        State("side_click", "data"),
    ],
)
def toggle_sidebar(n, nclick):
    if n:
        if nclick == "SHOW":
            sidebar_style = SIDEBAR_COLLAPSED
            content_style = CONTENT_STYLE1
            cur_nclick = "HIDDEN"
        else:
            sidebar_style = SIDEBAR_STYLE
            content_style = CONTENT_STYLE
            cur_nclick = "SHOW"
    else:
        sidebar_style = SIDEBAR_STYLE
        content_style = CONTENT_STYLE
        cur_nclick = "SHOW"

    return sidebar_style, content_style, cur_nclick


if __name__ == "__main__":
    app.run_server(debug=True, port=8086)
