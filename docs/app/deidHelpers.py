from dash import html
import pandas as pd
from dash import dash_table
import datetime, json
import jsonschema
from jsonschema import Draft7Validator
import settings as s
import io
import base64
import dash_ag_grid as dag

# Load the JSON schema
with open(s.SCHEMA_FILE) as file:
    schema = json.load(file)


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        # print(e)
        return html.Div(["There was an error processing this file."])

    # Validate the DataFrame
    df = validate_df(df)

    return html.Div(
        [
            html.H5(filename),
            html.H6(datetime.datetime.fromtimestamp(date)),
            # dash_table.DataTable(
            #     df.to_dict("records"),
            #     [{"name": i, "id": i} for i in df.columns],
            #     tooltip_data=[
            #         {
            #             column: {"value": str(value), "type": "markdown"}
            #             for column, value in row.items()
            #         }
            #         for row in df.to_dict("records")
            #     ],
            #     tooltip_duration=None,
            #     style_data_conditional=[],
            #     id="metadataTable",
            # ),
            dag.AgGrid(
                rowData=df.to_dict("records"),
                columnDefs=[{"headerName": i, "field": i} for i in df.columns],
                # For tooltips and other configurations, you would use the 'gridOptions' parameter
                # Example:
                # gridOptions={
                #     'enableToolPanel': True,
                #     'toolPanelSuppressRowGroups': True,
                #     ...
                # },
                id="dag_metadataTable",
            ),
            html.Hr(),  # horizontal line
            # For debugging, display the raw contents provided by the web browser
            html.Div("Raw Content"),
            html.Pre(
                contents[0:200] + "...",
                style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
            ),
        ]
    )


def validate_df(df):
    """Validate DataFrame against schema and return DataFrame with 'valid' column and 'error' column."""
    df["valid"] = True
    df["error_cols"] = ""

    validator = Draft7Validator(schema)
    for i, row in df.iterrows():
        row_dict = row.to_dict()

        error_list = validator.iter_errors(row_dict)
        error_tree = jsonschema.exceptions.ErrorTree(validator.iter_errors(row_dict))

        invalid_cols = []
        for e in error_list:
            ##pass
            invalid_cols.append(*e.path)
        if invalid_cols:
            print(",".join(invalid_cols))
        df.at[i, "valid"] = False
        df.at[i, "error_cols"] = str(invalid_cols)

    return df


def parse_testfile(filename):
    """This will parse a file that is local and hardcoded for demo purposes"""

    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(filename)
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(filename)
    except Exception as e:
        # print(e)
        return html.Div(["There was an error processing this file."])

    # Validate the DataFrame
    df = validate_df(df)

    return html.Div(
        [
            html.H5(filename),
            html.H6(datetime.datetime.now()),
            ### Trick since True becomes true in javascript
            dag.AgGrid(
                rowData=df.to_dict("records"),
                columnDefs=[{"headerName": i, "field": i} for i in df.columns],
                # For tooltips and other configurations, you would use the 'gridOptions' parameter
                # Example:
                # gridOptions={
                #     'enableToolPanel': True,
                #     'toolPanelSuppressRowGroups': True,
                #     ...
                # },
                id="metadataTable",
            ),
            # dash_table.DataTable(
            #     df.to_dict("records"),
            #     [{"name": i, "id": i} for i in df.columns],
            #     tooltip_data=[
            #         {
            #             column: {"value": str(value), "type": "markdown"}
            #             for column, value in row.items()
            #         }
            #         for row in df.to_dict("records")
            #     ],
            #     tooltip_duration=None,
            #     style_data_conditional=[
            #         {
            #             "if": {
            #                 "filter_query": "error_cols contains {}".format(column),
            #                 "column_id": column,
            #             },
            #             "backgroundColor": "red",
            #             "color": "white",
            #         }
            #         for column in df.columns
            #     ]
            #     + [
            #         {
            #             "if": {"column_id": column},
            #             "backgroundColor": "gray",
            #             "color": "white",
            #         }
            #         for column in df.columns
            #         if column not in schema["properties"]
            #     ],
            # ),
        ]
    )


def print_all_errors(error_tree):
    for error in error_tree.errors:
        print(f"Error at {list(error.path)}: {error.message}")
