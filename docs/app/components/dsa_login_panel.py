import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

# from dash_iconify import DashIconify
import settings as s
from girder_client import AuthenticationError
import girder_client

from settings import DSA_BASE_URL

## CReate initial girder client that just connects to the Prefefined host from the .env file

gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)


## Figure out the session related context here
login_state = dcc.Store(
    id="login-state",
    storage_type="memory",
    data={"logged_in": False, "username": None},
)


def getGc(apiKey=None, username=None, password=None, logOut=False):
    ### This will create a reference to the girder client
    global gc
    if "gc" not in globals():
        gc = girder_client.GirderClient(apiUrl=DSA_BASE_URL)

    if apiKey:
        gc.authenticate(apiKey=apiKey)

    elif logOut:
        gc.token = ""
        gc.session = ""
    elif username and password:
        gc.authenticate(username=username, password=password)

    return gc


login_modal = dbc.Modal(
    [
        dbc.ModalHeader("DSA Login Panel", className="bg-primary text-white"),
        dbc.ModalBody(
            [
                dbc.Input(
                    placeholder="Username",
                    id="username-input",
                    className="my-2 mb-3 ml-2   modal-input-height",
                    style={"maxWidth": 280},
                ),
                dbc.Input(
                    placeholder="Password",
                    id="password-input",
                    type="password",
                    className="mb-3 ml-2 modal-input-height",
                    style={"maxWidth": 280},
                ),
                dbc.Button(
                    "Authenticate",
                    id="authenticate-button",
                    color="primary",
                    className="ml-5 text-align-center mb-3 ",
                    style={"maxWidth": 200},
                ),
                html.Div(id="login-notification-body"),
            ],
            className="text-center",
        ),  # Message will be set here
    ],
    id="login-modal",
    is_open=False,
    centered=True,
    size="sm",
    className="text-dark",
)


dsa_login_panel = dmc.Grid(
    children=[
        dmc.Col(html.H1("NCI DeID Upload Agent"), span=3),
        dmc.Col(
            html.Span(
                [
                    dcc.Store(id="userName", data=None),
                    dmc.Text(
                        "Logged out",
                        id="userNameDisplay_text",
                        style={"fontSize": "20px", "marginRight": "10px"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center"},
            ),
            span=3,
            style={"display": "flex", "justifyContent": "flex-end"},
        ),
        login_modal,
        dmc.Col(
            dmc.Button(
                "Login",
                variant="filled",
                color="green",
                id="login-logout-button",
                # style={"marginRight": "30px", "display": "none"},
            ),
            span=2,
            style={"display": "flex", "justifyContent": "flex-end"},
        ),
    ],
    gutter="xl",
    justify="end",
)


dsa_login_panel = dbc.Container(
    [dsa_login_panel, login_state],
    fluid=True,
    style={"padding-top": "20px"},
)


@callback(
    [
        Output("login-state", "data"),
        Output("login-logout-button", "children"),
        Output("userNameDisplay_text", "children"),
        Output("login-modal", "is_open"),
        Output("login-notification-body", "children"),
    ],
    [
        Input("login-logout-button", "n_clicks"),
        Input("authenticate-button", "n_clicks"),
    ],
    [
        State("username-input", "value"),
        State("password-input", "value"),
        State("login-state", "data"),
        State("login-modal", "is_open"),
    ],
    prevent_initial_call=True,
)
def login_logout(
    n_clicks_login,
    n_clicks_authenticate,
    username,
    password,
    login_state,
    is_open,
):

    # global gc  ## Update the global gc state if needed
    ctx = dash.callback_context

    ## This should allow me to login automagically if the env key is set
    if not ctx.triggered:
        if s.DSAKEY:
            gc = getGc(apiKey=s.DSAKEY)
            tokenOwner = gc.get("user/me")["login"]
            return (
                {"logged_in": True, "username": tokenOwner},
                "Logout",
                f"Logged in as: {tokenOwner}",
                False,
                "",
            )
        return (
            {
                "logged_in": False,
                "username": None,
            },  ## Update the store letting me know I logged out
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "login-logout-button":

        if login_state["logged_in"]:
            ### NEED TO LOGOUT THE GirderClient!! Currently I wasn't logging out..

            getGc(logOut=True)  ## Logout the girder client..
            ## NEED TO SEE IF THIS ACTUALLY LOGS OUT THE SESSION OR RECONNECTS AS NO
            return (
                {"logged_in": False, "username": None},
                "Login",
                "Logged out",
                True,
                "",
            )
        return dash.no_update, dash.no_update, dash.no_update, True, ""
    elif button_id == "authenticate-button":
        if username and password:
            try:
                _ = getGc(username=username, password=password)
                ## TO DO... Catch if the login fails
                return (
                    {"logged_in": True, "username": username},
                    "Logout",
                    f"Logged in as: {username}",
                    False,
                    "",
                )
            except AuthenticationError:
                return (
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    dash.no_update,
                    "Login failed. Please check your credentials.",
                )

    return (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
