# Library imports
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import settings as s

from dash import (
    Dash,
    State,
    callback,
    callback_context,
    dcc,
    Input,
    Output,
    State,
    html,
)

from components.stores import stores
from components.header import header
from components.dsa_file_browser import dsa_file_browser
from components.metadata_upload_panel import metadata_upload_panel
from components.merged_dataview_panel import merged_dataview_panel
from components.instructions_panel import instructions_panel

external_stylesheets = [
    "https://codepen.io/chriddyp/pen/bWLwgP.css",
    dbc.themes.BOOTSTRAP,
]

app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

app.layout = dmc.NotificationsProvider(
    html.Div(
        [
            stores,
            html.Script(src="/assets/customRenderer.js"),
            header,
            html.Div(
                id={"type": "selected-folder", "id": "TBD", "level": 0},
                style={
                    "font-size": "20px",
                    "font-weight": "bold",
                    "margin-bottom": "20px",
                },
            ),
            html.Div(id="notifications-container"),
            html.Div(id="last-clicked-folder", style={"display": "none"}),
            dbc.Tabs(
                [
                    dbc.Tab(
                        dsa_file_browser,
                        label="Slides For DeID",
                        tab_id="slides-for-deid",
                    ),
                    dbc.Tab(
                        metadata_upload_panel,
                        label="Slide Metadata ",
                        tab_id="metadata",
                    ),
                    dbc.Tab(
                        merged_dataview_panel, label="Merged Data", tab_id="merged-data"
                    ),
                    dbc.Tab(
                        instructions_panel,
                        label="Instructions",
                        tab_id="intructions-tab",
                    ),
                ],
                active_tab="metadata",
            ),
        ]
    )
)

if __name__ == "__main__":
    ## Clear the log between restarts
    with open(s.log_filename, "w"):
        pass

    app.run(debug=True, host="0.0.0.0")
