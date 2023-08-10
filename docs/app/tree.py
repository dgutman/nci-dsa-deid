import dash, os
from dash.dependencies import Input, Output, State, MATCH
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc
import girder_client
from dash import dcc, html, callback
import settings as s

# # Replace with the base URL of your DSA
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
                style={"text-align": "left", "margin-left": f"{20*level}px"},
            ),
            html.Div(
                id={"type": "subfolders", "id": collection_folder["_id"], "level": level},
                style={"margin-left": f"{20*(level)}px"},
            ),
        ]
    )


tree_layout = html.Div(
    [
        dcc.Markdown("## Folder Tree"),
dmc.Grid(
    children=[
        dmc.Col(html.Div(), span=4),
        dmc.Col(dmc.TextInput(placeholder="Username",), span=3),
        dmc.Col(dmc.TextInput(placeholder="Password"), span=3),
        dmc.Col(dmc.Button("Login", variant="filled"), span=2),
    ],
    gutter="xl",
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
                    },
        ),
    ],
          style={
                        "border": "2px solid #ddd",  # Optional: adds a border around the div
                    },
)



@callback(
    Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
    Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
    [Input({"type": "folder", "id": MATCH, "level": MATCH}, "n_clicks")],
    [State({"type": "folder", "id": MATCH, "level": MATCH}, "id")],
    prevent_initial_call=True,
)
def toggle_folder(n_clicks, folder_id):
    if n_clicks % 2 == 1:  # folder was expanded
        level = folder_id["level"]
        if level == 1:
            subfolders = gc.get("folder?parentType=collection&parentId=%s" % folder_id["id"])
        else:
            subfolders = gc.get("folder?parentType=folder&parentId=%s" % folder_id["id"])

        if not subfolders:  # Check if subfolders list is empty
            return html.Div("No subfolders available."), DashIconify(icon="material-symbols:folder", width=20)
        return [
            html.Div(
                folder_div(subfolder),
            )
            for subfolder in subfolders
        ], DashIconify(icon="material-symbols:folder-open-rounded", width=20)
    else:  # folder was collapsed
        return [], DashIconify(icon="material-symbols:folder", width=20)
