import dash
from dash import dcc, html, Input, Output, State, callback_context, MATCH, ALL, callback
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import girder_client, json
import dash_mantine_components as dmc
import settings as s
import dash_ag_grid as dag

# # Replace with the base URL of  the DSA
gc = girder_client.GirderClient(apiUrl=s.DSA_BASE_URL)
collections = gc.get("collection")


def folder_div(collection_folder):
    if collection_folder["_modelType"] == "collection":
        level = 1
    else:
        level = 2

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
            "margin-top": "0px",
            "margin-bottom": "0px",
        },  # Adjust these values as needed
    )


tree_layout = html.Div(
    [
        dcc.Markdown("## Folder Tree"),
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
            },
        ),
    ],
    style={
        "border": "2px solid #ddd",  # Optional: adds a border around the div
    },
)


@callback(
    [
        Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "style"),
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

    if n_clicks % 2 == 1:  # folder was expanded
        level = folder_id["level"]

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
            children = [
                html.Div(
                    "No subfolders available.", style={"margin-left": f"{20*(level)}px"}
                )
            ]

    # Additional logic to handle style change:
    last_clicked_id = last_clicked_folder_data if last_clicked_folder_data else None
    if last_clicked_id == folder_id["id"]:
        style = {"color": "blue"}
    elif last_clicked_id:
        style = {"color": "blue"}
    else:
        style = {"color": "green"}

    return children, icon, style


# @callback(
#     [
#         Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
#         Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
#         Output({"type": "folder", "id": MATCH, "level": MATCH}, "style"),
#     ],
#     [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
#     [
#         State({"type": "folder", "id": MATCH, "level": MATCH}, "id"),
#         State("last_clicked_folder", "data"),
#     ],
#     prevent_initial_call=True,
# )
# def update_folder_styles_and_icons(n_clicks, folder_id, last_clicked_folder_data):
#     # Your original folder toggle logic:
#     if n_clicks % 2 == 1:  # folder was expanded
#         level = folder_id["level"]

#         if level == 1:
#             subfolders = gc.get(
#                 "folder?parentType=collection&parentId=%s" % folder_id["id"]
#             )
#         else:
#             subfolders = gc.get(
#                 "folder?parentType=folder&parentId=%s" % folder_id["id"]
#             )
#             itemList = gc.get(f"item?folderId={folder_id['id']}")

#         if not subfolders:  # Check if subfolders list is empty
#             return (
#                 html.Div(
#                     "No subfolders available.", style={"margin-left": f"{20*(level)}px"}
#                 ),
#                 DashIconify(icon="material-symbols:folder", width=20),
#                 {"color": "green"},
#             )
#         return (
#             [
#                 html.Div(
#                     folder_div(subfolder),
#                 )
#                 for subfolder in subfolders
#             ],
#             DashIconify(icon="material-symbols:folder-open-rounded", width=20),
#             {"color": "green"},
#         )
#     else:  # folder was collapsed
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"color": "blue"},
#         )

#     # Additional logic to handle style change:
#     last_clicked_id = last_clicked_folder_data if last_clicked_folder_data else None
#     if last_clicked_id == folder_id["id"]:
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"color": "blue"},
#         )
#     elif last_clicked_id:
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"color": "blue"},
#         )
#     else:
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"color": "green"},
#         )


# @callback(
#     [
#         Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
#         Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
#         Output({"type": "folder", "id": MATCH, "level": MATCH}, "style"),
#     ],
#     [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
#     [
#         State({"type": "folder", "id": MATCH, "level": MATCH}, "id"),
#         State("last_clicked_folder", "data"),
#     ],
#     prevent_initial_call=True,
# )
# def update_folder_styles_and_icons(n_clicks, folder_id, last_clicked_folder_data):
#     # Your original folder toggle logic:
#     if n_clicks % 2 == 1:  # folder was expanded
#         level = folder_id["level"]

#         if level == 1:
#             subfolders = gc.get(
#                 "folder?parentType=collection&parentId=%s" % folder_id["id"]
#             )
#         else:
#             subfolders = gc.get(
#                 "folder?parentType=folder&parentId=%s" % folder_id["id"]
#             )
#             itemList = gc.get(f"item?folderId={folder_id['id']}")

#         if not subfolders:  # Check if subfolders list is empty
#             return (
#                 html.Div(
#                     "No subfolders available.", style={"margin-left": f"{20*(level)}px"}
#                 ),
#                 DashIconify(icon="material-symbols:folder", width=20),
#                 {"font-color": "green"},
#             )
#         return (
#             [
#                 html.Div(
#                     folder_div(subfolder),
#                 )
#                 for subfolder in subfolders
#             ],
#             DashIconify(icon="material-symbols:folder-open-rounded", width=20),
#             {"font-color": "green"},
#         )
#     else:  # folder was collapsed
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"font-color": "blue"},
#         )

#     # Additional logic to handle style change:
#     last_clicked_id = last_clicked_folder_data if last_clicked_folder_data else None
#     if last_clicked_id == folder_id["id"]:
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"background-color": "blue"},
#         )
#     elif last_clicked_id:
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"background-color": "blue"},
#         )
#     else:
#         return (
#             [],
#             DashIconify(icon="material-symbols:folder", width=20),
#             {"background-color": "green"},
#         )


# @callback(
#     [
#         Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
#         Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
#     ],
#     [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
#     [State({"type": "folder", "id": MATCH, "level": MATCH}, "id")],
#     prevent_initial_call=True,
# )
# def toggle_folder(n_clicks, folder_id):
#     if n_clicks % 2 == 1:  # folder was expanded
#         level = folder_id["level"]

#         if level == 1:
#             subfolders = gc.get(
#                 "folder?parentType=collection&parentId=%s" % folder_id["id"]
#             )
#         else:
#             subfolders = gc.get(
#                 "folder?parentType=folder&parentId=%s" % folder_id["id"]
#             )
#             itemList = gc.get(f"item?folderId={folder_id['id']}")

#         if not subfolders:  # Check if subfolders list is empty
#             return (
#                 html.Div(
#                     "No subfolders available.", style={"margin-left": f"{20*(level)}px"}
#                 ),
#                 DashIconify(icon="material-symbols:folder", width=20),
#             )
#         return (
#             [
#                 html.Div(
#                     folder_div(subfolder),
#                 )
#                 for subfolder in subfolders
#             ],
#             DashIconify(icon="material-symbols:folder-open-rounded", width=20),
#         )
#     else:  # folder was collapsed
#         return [], DashIconify(icon="material-symbols:folder", width=20)


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

    # triggered_id = json.loads(callback_context.triggered[0]["prop_id"].split(".")[0])[
    #     "id"
    # ]

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
        dbc.Button(
            "Sidebar",
            outline=True,
            color="secondary",
            className="mr-1",
            id="btn_sidebar",
        ),
        dbc.NavItem(dbc.NavLink("Page 1", href="#")),
    ],
    brand="NCI DSA DeID",
    brand_href="#",
    color="dark",
    dark=True,
    fluid=True,
)


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
    "left": "-30rem",
    "bottom": 0,
    "width": "16rem",
    "height": "100%",
    "z-index": 1,
    "overflow-x": "hidden",
    "transition": "all 0.5s",
    "padding": "0rem 0rem",
    "background-color": "#f8f9fa",
}

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

# @callback(
#     [
#         Output({"type": "subfolders", "id": ALL, "level": ALL}, "children"),
#         Output({"type": "folder", "id": ALL, "level": ALL}, "leftIcon"),
#         Output({"type": "folder", "id": ALL, "level": ALL}, "style"),
#     ],
#     [Input('reset-button', 'n_clicks')],
#     prevent_initial_call=True
# )
# def reset_tree(n_clicks):
#     # Return empty children to collapse all folders
#     empty_children = [dash.no_update] * len(collections)

#     # Return the folder icon to all folders
#     folder_icons = [DashIconify(icon="material-symbols:folder", width=20)] * len(collections)

#     # Return the original blue color to all folders
#     folder_styles = [{"background-color": "blue", "text-align": "left", "padding": "2px 8px


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
