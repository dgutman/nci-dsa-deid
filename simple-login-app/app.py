from dash import Dash, html, Input, Output, callback, State, no_update, dcc
import dash_bootstrap_components as dbc
from girder_client import GirderClient
from dash_ag_grid import AgGrid
import requests

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

app.layout = html.Div(
    [
        dcc.Store(id="user-store", data={}),
        html.Div(
            [
                html.Div("Logged out", id="username-status"),
                dbc.Button("Login", id="login-btn", style={"margin-left": 10}),
            ],
            style={"display": "flex"},
        ),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Log in")),
                dbc.ModalBody(
                    [
                        html.Div("Login or email", style={"fontWeight": "bold"}),
                        dbc.Input(placeholder="Enter login", id="username"),
                        html.Div(
                            "Password", style={"fontWeight": "bold", "marginTop": 10}
                        ),
                        dbc.Input(
                            placeholder="Enter password", type="password", id="password"
                        ),
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button("Login", className="ms-auto", id="authenticate-btn")
                ),
            ],
            id="modal",
            is_open=False,
        ),
        # dbc.Button("Get collections", id="get-collections-btn"),
        AgGrid(
            id="collections-grid",
            columnDefs=[
                {"field": "_id"},
                {"field": "name"},
                {"field": "public"},
                {"field": "size"},
                {"field": "updated"},
            ],
            rowData=[],
        ),
    ]
)


@callback(
    [
        Output("modal", "is_open", allow_duplicate=True),
        Output("login-btn", "children", allow_duplicate=True),
        Output("username-status", "children", allow_duplicate=True),
        Output("user-store", "data", allow_duplicate=True),
    ],
    [Input("login-btn", "n_clicks"), State("login-btn", "children")],
    prevent_initial_call=True,
)
def login_modal(n_clicks: int, login_value: str):
    """Open the login modal."""
    if n_clicks:
        if login_value == "Login":
            return True, no_update, no_update, no_update
        else:
            return False, "Login", "Logged out", []

    return False, no_update, no_update, no_update


@callback(
    [
        Output("user-store", "data", allow_duplicate=True),
        Output("modal", "is_open", allow_duplicate=True),
        Output("username-status", "children", allow_duplicate=True),
        Output("login-btn", "children", allow_duplicate=True),
    ],
    [
        Input("authenticate-btn", "n_clicks"),
        State("username", "value"),
        State("password", "value"),
    ],
    prevent_initial_call=True,
)
def authenticate(n_clicks: int, username: str, password: str):
    if n_clicks:
        gc = GirderClient(apiUrl="https://megabrain.neurology.emory.edu/api/v1")

        try:
            gc.authenticate(username=username, password=password)

            token = gc.get("user/authentication")["authToken"]["token"]

            return [token], False, username, "logout"
        except:
            # Failed to authenticate!
            return [], no_update, no_update, no_update

    return [], False, no_update, no_update


@callback(Output("collections-grid", "rowData"), Input("user-store", "data"))
def update_collection_grid(data):
    # Get the token.
    if data:
        header = {"Girder-Token": data[0]}
    else:
        header = {}

    response = requests.get(
        "https://megabrain.neurology.emory.edu/api/v1/collection?limit=50&offset=0&sort=name&sortdir=1",
        headers=header,
    )

    if response.status_code == 200:
        return response.json()

    return no_update


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", threaded=True)
