import dash_bootstrap_components as dbc
from deidHelpers import parse_testfile, validate_df, parse_contents
import dash
import dash_ag_grid as dag

# import dash_daq as daq
import dash_mantine_components as dmc
import dash_renderjson
import pandas as pd
from dash import (
    Dash,
    Input,
    Output,
    State,
    callback,
    callback_context,
    dash_table,
    dcc,
    html,
)
from jsonschema import Draft7Validator, validate
from jsonschema.exceptions import ErrorTree
import settings as s
import dash_daq as daq
import datetime, base64, json, jsonschema
import tree
from dash import MATCH

# import deidHelpers as hlprs

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

# Load the JSON schema
with open(s.SCHEMA_FILE) as file:
    schema = json.load(file)

modal_tree = dbc.Container(
    [
        # Trigger button
        tree.dsa_login_panel,
        # Modal
        dbc.Modal(
            [
                dbc.ModalHeader("Select Folder For DeID"),
                dbc.ModalBody(tree.tree_layout),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal-btn", className="ml-auto")
                ),
            ],
            id="selectDSAfolder-modal",
        ),
    ]
)
tab1_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("Target Images", className="card-text"),
            dbc.Button("Click here", color="success"),
        ]
    ),
    className="mt-3",
)

tab2_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("Images for DeID", className="card-text"),
            dbc.Button("Check Matches", id="check-match-button"),
            html.Div(id="itemListinfo"),
        ]
    ),
    className="mt-3",
)


metadata_upload_layout = dbc.Container(
    [
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=False,
        ),
        html.Div(id="output-data-upload"),
    ]
)

debug_buttons = html.Div(
    [
        dbc.Button(
            "Get DeidFiles",
            id="load-files-for-deid-button",
            color="info",
        ),
        dbc.Button(
            "Load Test Data",
            id="load-test-data-button",
        ),
    ]
)

merged_data = html.Div([html.Div(id="mergedImageSet")])

tabs = dbc.Tabs(
    [
        dbc.Tab(tab2_content, label="Slides For DeID"),
        dbc.Tab(metadata_upload_layout, label="Metadata "),
        dbc.Tab(debug_buttons, label="Debug Tools"),
        dbc.Tab(merged_data, label="merged Data"),
    ]
)


app.layout = html.Div(
    [
        html.Div(
            id={"type": "selected-folder", "id": "TBD", "level": 0},
            style={"font-size": "20px", "font-weight": "bold", "margin-bottom": "20px"},
        ),
        modal_tree,
        dcc.Store(id="itemList_store"),
        dcc.Store(id="metadata_store"),
        dcc.Store(id="mergedItem_store"),
        dcc.Store({"type": "datastore", "id": "ils", "level": 2}),
        html.Div(id="last-clicked-folder", style={"display": "none"}),
        tabs,
        # dbc.Card([dbc.CardBody(schema_layout, class_name="mb-3")]),
    ]
)


@app.callback(
    Output("mergedItem_store", "data"),  # Replace with your DataTable's ID
    [Input("check-match-button", "n_clicks")],
    [State("metadata_store", "data"), State("itemList_store", "data")],
    prevent_initial_call=True,
)
def check_name_matches(n, metadata, itemlist_data):
    print("I like matching")

    if not n:
        raise dash.exceptions.PreventUpdate

    #     # Extract the 'name' column from the parsed contents DataTable
    filenames_from_metadata = set(row["InputFileName"] for row in metadata)
    #     # Extract the 'name' column from the itemList table
    itemlist_names = set(row["name"] for row in itemlist_data)
    print(len(metadata), "rows are in the metadata table")
    print(len(itemlist_data), "rows are in the current itemlist")

    try:
        for row in itemlist_data:
            row["match_result"] = (
                "Match" if row["name"] in filenames_from_metadata else "No Match"
            )
        return itemlist_data
    except:
        print("Something broke")


@app.callback(Output("mergedImageSet", "children"), Input("mergedItem_store", "data"))
def updateMergedDatatable(mergeddata):
    if mergeddata:
        print(mergeddata[0]["name"])
        # print("yo   ")

        merged_grid = [
            dag.AgGrid(
                rowData=mergeddata,
                columnDefs=[
                    {"headerName": i, "field": i} for i in mergeddata[0].keys()
                ],
                # For tooltips and other configurations, you would use the 'gridOptions' parameter
                # Example:
                # gridOptions={
                #     'enableToolPanel': True,
                #     'toolPanelSuppressRowGroups': True,
                #     ...
                # },
            )
        ]

        return merged_grid
    else:
        return [html.Div()]


#     # Update the parsed contents DataTable with match results
#     print("HII Dave")


#     return datatable_data


@app.callback(
    Output("selectDSAfolder-modal", "is_open"),
    [Input("open-modal-btn", "n_clicks"), Input("close-modal-btn", "n_clicks")],
    [State("selectDSAfolder-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@callback(
    Output("output-data-upload", "children"),
    Input("load-test-data-button", "n_clicks"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_output(testdata_n_clicks, list_of_contents, list_of_names, list_of_dates):
    if testdata_n_clicks or s.TEST_MODE:
        print("test data loader pushed")
        return parse_testfile(s.TEST_FILENAME)

    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d)
            for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)
        ]
        return children


## To refactor... the metadata store should be populating the metadatatable , not vice
@callback(Output("metadata_store", "data"), Input("metadataTable", "rowData"))
def updateMetadataStore(metadata):
    print(len(metadata))
    return metadata


if __name__ == "__main__":
    app.run(debug=True)


# I am trying to set up conditional formatting so that if the column name appears in the row error_cols it will highlight that cell in orange
