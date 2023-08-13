# Standard Libraries
import json
import datetime

# Third-party libraries
import dash_bootstrap_components as dbc
import dash
import dash_ag_grid as dag
import dash_daq as daq
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
from jsonschema import Draft7Validator

# Local modules
from deidHelpers import parse_testfile, validate_df, parse_contents
from components.modals import modal_tree
from components.tabs import tab1_content, tab2_content
from components.trees import (
    dsa_login_panel,
)  # Replace with specific components you need
import settings as s


external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

schema = s.SCHEMA

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

# tabs = dbc.Tabs(
#     [
#         dbc.Tab(tab2_content, label="Slides For DeID"),
#         dbc.Tab(metadata_upload_layout, label="Metadata "),
#         dbc.Tab(debug_buttons, label="Debug Tools"),
#         dbc.Tab(merged_data, label="merged Data"),
#     ]
# )

tabs = dbc.Tabs(
    [
        dbc.Tab(tab2_content, label="Slides For DeID", tab_id="slides-for-deid"),
        dbc.Tab(metadata_upload_layout, label="Metadata ", tab_id="metadata"),
        dbc.Tab(debug_buttons, label="Debug Tools", tab_id="debug-tools"),
        dbc.Tab(merged_data, label="merged Data", tab_id="merged-data"),
    ],
    id="main-tabs",
)


app.layout = html.Div(
    [
        html.Div(
            id={"type": "selected-folder", "id": "TBD", "level": 0},
            style={"font-size": "20px", "font-weight": "bold", "margin-bottom": "20px"},
        ),
        modal_tree,
        dsa_login_panel,
        dcc.Store(id="itemList_store", data=s.defaultItemList),
        dcc.Store(id="metadata_store"),
        dcc.Store(id="mergedItem_store"),
        dcc.Store({"type": "datastore", "id": "ils", "level": 2}),
        html.Div(id="last-clicked-folder", style={"display": "none"}),
        tabs,
        # dbc.Card([dbc.CardBody(schema_layout, class_name="mb-3")]),
    ]
)


@app.callback(
    [
        Output("mergedItem_store", "data"),
        Output("main-tabs", "active_tab"),  # Add this line
    ],
    [Input("check-match-button", "n_clicks")],
    [State("metadata_store", "data"), State("itemList_store", "data")],
    prevent_initial_call=True,
)
def check_name_matches(n, metadata, itemlist_data):
    if not n:
        raise dash.exceptions.PreventUpdate

    # Create a mapping from filename to its metadata
    metadata_mapping = {row["InputFileName"]: row for row in metadata}

    print(len(metadata), "rows are in the metadata table")
    print(len(itemlist_data), "rows are in the current itemlist")

    try:
        for row in itemlist_data:
            if row["name"] in metadata_mapping:
                row["match_result"] = "Match"
                matched_metadata = metadata_mapping[row["name"]]
                for col in s.COLS_FOR_COPY:
                    if (
                        col in matched_metadata
                    ):  # Ensure the column exists in the metadata
                        row[col] = matched_metadata[col]
            else:
                row["match_result"] = "No Match"
            row["valid"] = True
        return itemlist_data, "merged-data"
    except Exception as e:
        print("Something broke:", e)
        return None, "merged-data"


# def check_name_matches(n, metadata, itemlist_data):
#     if not n:
#         raise dash.exceptions.PreventUpdate

#     #     # Extract the 'name' column from the parsed contents DataTable
#     filenames_from_metadata = set(row["InputFileName"] for row in metadata)
#     #     # Extract the 'name' column from the itemList table
#     itemlist_names = set(row["name"] for row in itemlist_data)
#     print(len(metadata), "rows are in the metadata table")
#     print(len(itemlist_data), "rows are in the current itemlist")

#     try:
#         for row in itemlist_data:
#             row["match_result"] = (
#                 "Match" if row["name"] in filenames_from_metadata else "No Match"
#             )
#             row["valid"] = True
#         return itemlist_data, "merged-data"
#     except:
#         print("Something broke")


@app.callback(Output("mergedImageSet", "children"), Input("mergedItem_store", "data"))
def updateMergedDatatable(mergeddata):
    if mergeddata:
        for row in mergeddata:
            if row["match_result"] == "Match":
                row["match_result_style"] = {"backgroundColor": "orange"}
            else:
                row["match_result_style"] = {}

            if row["valid"]:
                row["valid_style"] = {"backgroundColor": "green"}
            else:
                row["valid_style"] = {}

        merged_grid = [
            dag.AgGrid(
                rowData=mergeddata,
                columnSize="autoSize",
                columnDefs=s.MERGED_COL_DEFS,
                defaultColDef=dict(
                    resizable=True,
                    editable=True,
                    minWidth=50,
                    sortable=True,
                    maxWidth=150,
                    columnSize="autoSize",
                    cellStyle={
                        "styleConditions": [
                            {
                                "condition": "params.value == 72000",
                                "style": {"color": "orange"},
                            },
                            {
                                "condition": "params.value == 'Match'",
                                "style": {
                                    "backgroundColor": "purple",
                                    "color": "white",
                                },
                            },
                            {
                                "condition": "params.colDef.headerName == 'Make'",
                                "style": {"backgroundColor": "red", "color": "yellow"},
                            },
                        ]
                    },
                ),
                dashGridOptions={"toolTipShowDelay": 10, "rowSelection": "single"}
                # defaultColDef=dict(
                #     resizable=True,
                #     cellStyle={
                #         "styleConditions": [
                #             {
                #                 "condition": "param.value == 'Match",
                #                 "style": {"color": "green"},
                #             }
                #         ]
                #     },
                # ),
                # # dashGridOptions={
                #     "getRowStyle": """
                #     function(params) {
                #         if (params.node.data.match_result == 'Match') {
                #             return params.node.data.match_result_style;
                #         }
                #         if (params.node.data.valid) {
                #             return params.node.data.valid_style;
                #         }
                #     }
                #     """
                # },
            )
        ]
        return merged_grid
    else:
        return [html.Div()]


# @app.callback(Output("mergedImageSet", "children"), Input("mergedItem_store", "data"))
# def updateMergedDatatable(mergeddata):
#     if mergeddata:
#         for row in mergeddata:
#             if row["match_result"] == "Match":
#                 row["match_result_style"] = {"backgroundColor": "orange"}
#             if row["valid"]:
#                 row["valid_style"] = {"backgroundColor": "green"}

#         merged_grid = [
#             dag.AgGrid(
#                 rowData=mergeddata,
#                 columnDefs=s.MERGED_COL_DEFS,
#                 cellStyle={"field": "match_result", "styleField": "match_result_style"},
#                 cellStyle={"field": "valid", "styleField": "valid_style"},
#             )
#         ]
#         return merged_grid
#     else:
#         return [html.Div()]


# In this approach, we're computing the styles in Python and adding them to each row in the rowData. The cellStyle property in dag.AgGrid is then used to apply these styles based on the specified conditions.

# However, please note that I'm making an assumption about how dag.AgGrid works based on your previous code and the error you encountered. The exact implementation might differ, and you may need to refer to the documentation for dag.AgGrid to ensure you're using the correct properties and syntax.


# def updateMergedDatatable(mergeddata):
#     if mergeddata:
#         print(mergeddata[0]["name"])
#         # print("yo   ")

#         merged_grid = [
#             dag.AgGrid(
#                 rowData=mergeddata,
#                 columnDefs=s.MERGED_COL_DEFS
#                 # [
#                 #     {"headerName": i, "field": i} for i in mergeddata[0].keys()
#                 # ],
#                 # For tooltips and other configurations, you would use the 'gridOptions' parameter
#                 # Example:
#                 # gridOptions={
#                 #     'enableToolPanel': True,
#                 #     'toolPanelSuppressRowGroups': True,
#                 #     ...
#                 # },
#             )
#         ]

#         return merged_grid
#     else:
#         return [html.Div()]


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
    # print(len(metadata))
    return metadata


if __name__ == "__main__":
    app.run(debug=True)


# I am trying to set up conditional formatting so that if the column name appears in the row error_cols it will highlight that cell in orange
