# components/tabs.py

import dash_bootstrap_components as dbc
from dash import html

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

