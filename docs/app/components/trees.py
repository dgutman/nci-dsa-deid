import dash, os
from dash import callback_context
from dash.dependencies import Input, Output, State, MATCH, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import dash_bootstrap_components as dbc
import girder_client, json
from dash import dcc, html, callback
import settings as s
import dash_ag_grid as dag

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


# )
@callback(
    [
        Output({"type": "subfolders", "id": MATCH, "level": MATCH}, "children"),
        Output({"type": "folder", "id": MATCH, "level": MATCH}, "leftIcon"),
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


@callback(Output("itemListinfo", "children"), [Input("itemList_store", "data")])
def dumpItemList(itemList):
    if itemList:
        print(len(itemList))
        ## Make this into a datatable...
        itemTable = dag.AgGrid(
            id="itemGrid",
            columnDefs=[
                {"field": "name"},
                {"field": "size"},
                {"field": "_id"},
                {"field": "match_result"},
            ],
            rowData=itemList,
            defaultColDef={"flex": 1},
        )
        return itemTable
        # return html.Div(json.dumps(itemList, indent=2))


@callback(
    Output("itemList_store", "data"),
    [Input({"type": "folder", "id": ALL, "level": ALL}, "n_clicks")],
    [State({"type": "folder", "id": ALL, "level": ALL}, "id")],
    prevent_initial_call=True,
)
def update_recently_clicked_folder(folder_id, n_clicks):
    # print(folder_id, n_clicks)
    trigger = callback_context.triggered[0]
    print(trigger["prop_id"])

    prop_id_string = trigger["prop_id"].rsplit(".", 1)[0]
    prop_id_dict = json.loads(prop_id_string)

    # prop_id_dict = json.loads(trigger["prop_id"].split(".")[0])

    # Now you can extract the desired values from the dictionary
    level = prop_id_dict["level"]
    folder_type = prop_id_dict["type"]
    folder_id = prop_id_dict["id"]
    print(level, folder_type, folder_id)

    if level == 2:
        itemListInfo = list(gc.listItem(folder_id))
        # print(itemListInfo)
        return itemListInfo

    return {}
