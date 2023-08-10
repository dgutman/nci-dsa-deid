import dash_bootstrap_components as dbc
# import dash_daq as daq
import dash_mantine_components as dmc
import dash_renderjson
import pandas as pd
from dash import (Dash, Input, Output, State, callback, callback_context,
                  dash_table, dcc, html)
from jsonschema import Draft7Validator, ErrorTree, validate
import settings as s
import dash_daq as daq
import datetime, base64, json, jsonschema
import tree
#import deidHelpers as hlprs

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',dbc.themes.BOOTSTRAP]
app = Dash(__name__, external_stylesheets=external_stylesheets)

def print_all_errors(error_tree):
    for error in error_tree.errors:
        print(f"Error at {list(error.path)}: {error.message}")


# Load the JSON schema
with open(s.SCHEMA_FILE) as file:
    schema = json.load(file)


def validate_df(df):
    """Validate DataFrame against schema and return DataFrame with 'valid' column and 'error' column."""
    df['valid'] = True
    df['error_cols'] = ""

    validator = Draft7Validator(schema)
    for i, row in df.iterrows():
        row_dict = row.to_dict()

        error_list = validator.iter_errors(row_dict)
        error_tree = jsonschema.exceptions.ErrorTree(validator.iter_errors(row_dict))


        invalid_cols = []
        for e in error_list:
            ##pass
            invalid_cols.append(*e.path)
        print(",".join(invalid_cols))
        df.at[i, 'valid'] = False
        df.at[i, 'error_cols'] = str(invalid_cols)

    return df


schema_layout =dbc.Card([ 
daq.ToggleSwitch(id="my-toggle-switch", value=False), 
dbc.CardBody(id="schema-output")],
         style={"width": "18rem"})


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        # print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    # Validate the DataFrame
    df = validate_df(df)

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            tooltip_data=[
                {
                    column: {'value': str(value), 'type': 'markdown'}
                    for column, value in row.items()
                } for row in df.to_dict('records')
            ],
            tooltip_duration=None,
            style_data_conditional=[
                            ]
        ),
        html.Hr(),  # horizontal line
        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

def parse_testfile(filename):
    """This will parse a file that is local and hardcoded for demo purposes"""

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(filename)
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(filename)
    except Exception as e:
        # print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    # Validate the DataFrame
    df = validate_df(df)

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.now()),
### Trick since True becomes true in javascript

        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            tooltip_data=[
                {
                    column: {'value': str(value), 'type': 'markdown'}
                    for column, value in row.items()
                } for row in df.to_dict('records')
            ],
            tooltip_duration=None,
            style_data_conditional=[
            {
                'if': {
                    'filter_query': 'error_cols contains {}'.format(column),                     'column_id': column
                },
                'backgroundColor': 'red',
                'color': 'white'}
             for column in df.columns
        ] 
        + [
            {
                'if': {
                    'column_id': column
                },
                'backgroundColor': 'gray',
                'color': 'white'
            } for column in df.columns if column not in schema['properties']
            ]
        )
    ])

app.layout = html.Div([
    html.H1("NCI DeID Upload Agent"),
    dcc.Store(id='itemList_store'),
    tree.tree_layout,
    html.Div([html.Button("Load Test Data",id="load-test-data-button"),
              html.Button("Get DeidFiles",id="load-files-for-deid-button")]),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),
    dbc.Card([dbc.CardBody(schema_layout,class_name="mb-3")])
])


@app.callback(Output("schema-output", "children"), [Input("my-toggle-switch", "value")])
def display_output(value):
    if value:
        data = {"a": 1, "b": [1, 2, 3, {"c": 4}]}
        theme = {
            "scheme": "monokai",
            "author": "wimer hazenberg (http://www.monokai.nl)",
            "base00": "#272822",
            "base01": "#383830",
            "base02": "#49483e",
            "base03": "#75715e",
            "base04": "#a59f85",
            "base05": "#f8f8f2",
            "base06": "#f5f4f1",
            "base07": "#f9f8f5",
            "base08": "#f92672",
            "base09": "#fd971f",
            "base0A": "#f4bf75",
            "base0B": "#a6e22e",
            "base0C": "#a1efe4",
            "base0D": "#66d9ef",
            "base0E": "#ae81ff",
            "base0F": "#cc6633",
        }
        return dash_renderjson.DashRenderjson(id="input", data=schema, max_depth=-1, theme=theme, invert_theme=True)

@callback(Output('output-data-upload', 'children'),
          Input('load-test-data-button','n_clicks'),
          Input('upload-data', 'contents'),
          State('upload-data', 'filename'),
          State('upload-data', 'last_modified'))
def update_output(testdata_n_clicks,list_of_contents, list_of_names, list_of_dates):
    if testdata_n_clicks or s.TEST_MODE:
        print("test data loader pushed")
        return parse_testfile(s.TEST_FILENAME)

    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

if __name__ == '__main__':
    app.run_server(debug=True)


#I am trying to set up conditional formatting so that if the column name appears in the row error_cols it will highlight that cell in orange