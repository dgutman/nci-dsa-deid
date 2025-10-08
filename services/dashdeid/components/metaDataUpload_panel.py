from dash import dcc, html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
from utils.deidHelpers import parse_testfile, parse_contents
import settings as s


metadata_upload_layout = dbc.Container(
    [
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
