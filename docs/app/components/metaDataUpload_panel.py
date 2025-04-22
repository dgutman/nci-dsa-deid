from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from utils.deidHelpers import parse_testfile, parse_contents
import settings as s
import pandas as pd


metadata_upload_layout = dbc.Container(
    [
        # Add a link for downloading the CSV template
        html.Div(
            [
                dbc.Button("Download CSV Template", id="btn_csv_template"),
                dcc.Download(id="download-template-csv"),
            ],
            style={
                "display": "flex",
                "justifyContent": "center",
                "marginBottom": "5px",
                "marginTop": "5px",
            },
        ),
        html.Div(
            "Please drag and drop a CSV file containing metadata linked to the slides of interest below"
        ),
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


@callback(
    Output("download-template-csv", "data"),
    Input("btn_csv_template", "n_clicks"),
    prevent_initial_call=True,
)
def download_template(n_clicks):
    if n_clicks:
        df = pd.read_csv("exampleData_112322.csv")
        return dcc.send_data_frame(df.to_csv, "deidTemplate.csv")

    return no_update


## Changing this to deal with only a single input..
@callback(
    Output("output-data-upload", "children"),
    Output("metadata_store", "data"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
    prevent_initial_call=True,
)
def update_output(file_content, file_name, file_upload_date):
    if s.TEST_MODE:
        uploaded_file_layout, uploaded_file_data = parse_contents(
            "TEST_FILE", s.TEST_FILENAME, file_upload_date
        )

        return [uploaded_file_layout], uploaded_file_data

    ### TO DO:  Handle exception better, may want to use the mantine_notification provider
    valid_extensions = ("csv", "xlsx")

    if file_name.endswith(valid_extensions):
        print("Valid extension found")
    else:
        print("Invalid exception found")
        return [html.Div()], {}
    ### Check and see if the file_name ends with .csv or .xlsx

    if file_content is not None:
        uploaded_file_layout, uploaded_file_data = parse_contents(
            file_content, file_name, file_upload_date
        )

        return [uploaded_file_layout], uploaded_file_data

    return [html.Div()], {}
