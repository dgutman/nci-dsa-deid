# components/tabs.py
import dash_bootstrap_components as dbc
from dash import html
from components.modals import modal_tree
from components.trees import openTreeModal

tab1_content = dbc.Card(
    dbc.CardBody(
        [
            html.P("Target Images", className="card-text"),
            dbc.Button("Click here", color="success"),
        ]
    ),
    className="mt-3",
)

slideListTab_content = dbc.Card(
    dbc.CardBody(
        [
            # html.P("Images for DeID", className="card-text"),
            dbc.Button("Match Metadata", id="check-match-button", className="me-2"),
            dbc.Button("JustDeID", id="no-meta-deid-button", className="me-1"),
            openTreeModal,
            modal_tree,
            html.Div(id="itemListinfo"),
        ]
    ),
    className="mt-4",
    style={"height": "100%"},
)
