import dash, os
from dash import callback_context
from dash.dependencies import Input, Output, State, MATCH, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc
import girder_client
from dash import dcc, html, callback
import settings as s

# # Replace with the base URL of    r DSA
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
                    "margin-left": f"{20*level}px",
                    "padding": "2px 8px",
                    "font-size": "1rem",
                    "height": "18px",
                },
            ),
            html.Div(
                id={
                    "type": "subfolders",
                    "id": collection_folder["_id"],
                    "level": level,
                },
                style={"margin-left": f"{20*(level)}px"},
            ),
        ],
        style={
            "margin-top": "0px",
            "margin-bottom": "0px",
        },  # Adjust these values as needed
    )


dsa_login_panel = dmc.Grid(
    children=[
        dmc.Col(html.H1("NCI DeID Upload Agent"), span=3),
        dmc.Col(
            html.Span(
                [
                    dbc.Button("DSA Folder", id="open-modal-btn", className="me-1"),
                    dbc.Button(
                        "Load Test Data",
                        id="load-test-data-button",
                    ),
                    dbc.Button(
                        "Get DeidFiles",
                        id="load-files-for-deid-button",
                        color="info",
                    ),
                ]
            ),
            span=3,
        ),
        dmc.Col(
            dmc.TextInput(
                placeholder="Username",
            ),
            span=2,
        ),
        dmc.Col(dmc.TextInput(placeholder="Password"), span=2),
        dmc.Col(dmc.Button("Login", variant="filled"), span=1),
    ],
    gutter="xl",
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


# @callback(
#     Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
#     Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
#     [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
#     [State({"type": "folder", "id": MATCH, "level": MATCH}, "id")],
#     prevent_initial_call=True,
# )
@callback(
    [
        Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
        # Output(
        #     {"type": "datastore", "id": ALL, "level": ALL}, "data"
        # ),  # <-- Added this output
    ],
    [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
    [State({"type": "folder", "id": MATCH, "level": MATCH}, "id")],
    prevent_initial_call=True,
)
def toggle_folder(n_clicks, folder_id):
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

        if not subfolders:  # Check if subfolders list is empty
            return (
                html.Div("No subfolders available."),
                DashIconify(icon="material-symbols:folder", width=20),
            )
        return (
            [
                html.Div(
                    folder_div(subfolder),
                )
                for subfolder in subfolders
            ],
            DashIconify(icon="material-symbols:folder-open-rounded", width=20),
        )
    else:  # folder was collapsed
        return [], DashIconify(icon="material-symbols:folder", width=20)


@callback(
    # Output({"type": "selected-folder", "id": MATCH, "level": MATCH}, "children"),
    Output("garfield", "children"),
    [Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks")],
    [State({"type": "folder", "id": ALL, "level": ALL}, "id")],
)
def update_recently_clicked_folder(folder_id, n_clicks):
    print(folder_id, n_clicks)
    trigger = callback_context.triggered[0]
    print(trigger)
    return html.Div("I like folders")


# @callback(
#     Output("itemList_store", "data"),
#     [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
#     [State({"type": "folder", "id": MATCH, "level": MATCH}, "id")],
#     prevent_initial_call=True,
# )
# def update_item_list(n_clicks, folder_id):
#     itemList = gc.get(f"item?folderId={folder_id['id']}")
#     print("YOYOYOYOYO")
#     return itemList


# @callback(
#     Output({"type": "itemList_store"}, "data"),
#     [
#         Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")
#     ],  # Here, use a specific ID
#     prevent_initial_call=True,
# )
# def update_item_list(n_clicks, folder_id):
#     # ... (code to update the item list based on the folder_id)
#     print("HELLO WORLD???")
#     print(n_clicks)
#     itemList = gc.get(f"item?folderId={folder_id}")
#     print(len(itemList), "items in my item list")
#     return itemList
