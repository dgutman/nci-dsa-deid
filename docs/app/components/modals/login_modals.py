# Modal for login in.
from dash import Input, Output, State, html, callback, no_update
import dash_bootstrap_components as dbc
from girder_client import GirderClient
from os import getenv

login_modal = dbc.Modal(
    [
        dbc.ModalHeader("Log in"),
        dbc.ModalBody(
            [
                html.Div("Login or email", style={"margin": 5, "fontWeight": "bold"}),
                dbc.Input(
                    id="login",
                    type="text",
                    placeholder="Enter login",
                    style={"margin": 5},
                ),
                html.Div(
                    "Password",
                    style={"margin": 5, "marginTop": 15, "fontWeight": "bold"},
                ),
                dbc.Input(
                    id="password",
                    type="password",
                    placeholder="Enter password",
                    style={"margin": 5},
                ),
                html.Div(
                    "Login failed.",
                    hidden=True,
                    id="login-failed",
                    style={"color": "red", "fontWeight": "bold", "margin": 10},
                ),
            ],
        ),
        dbc.ModalFooter(
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "Close",
                            id="close-login-modal",
                            className="me-1",
                            color="light",
                        )
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Login",
                            id="log-in-btn",
                            className="me-1",
                            color="primary",
                        )
                    ),
                ],
            )
        ),
    ],
    is_open=False,
    id="login-modal",
)

logout_modal = dbc.Modal(
    [
        dbc.ModalFooter(
            [
                dbc.Button(
                    "Log out",
                    id="logout-btn",
                    color="danger",
                    className="me-1",
                ),
            ]
        )
    ],
    is_open=False,
    id="logout-modal",
)


# Callbacks
@callback(
    [
        Output("login-modal", "is_open", allow_duplicate=True),
        Output("logout-modal", "is_open", allow_duplicate=True),
    ],
    [Input("login-btn", "n_clicks"), State("login-btn", "children")],
    prevent_initial_call=True,
)
def open_login_modal(n_clicks, children):
    # Open login / logout modal.
    if n_clicks:
        if children == "Log in":
            return True, False
        else:
            return False, True

    return False, False


@callback(
    [
        Output("user-store", "data"),
        Output("login-failed", "hidden", allow_duplicate=True),
        Output("login-modal", "is_open", allow_duplicate=True),
        Output("login", "value", allow_duplicate=True),
        Output("password", "value", allow_duplicate=True),
    ],
    [
        Input("log-in-btn", "n_clicks"),
        State("login", "value"),
        State("password", "value"),
    ],
    prevent_initial_call=True,
)
def login(n_clicks, login, password):
    # Try to login.
    gc = GirderClient(apiUrl=getenv("DSA_API_URL"))

    try:
        _ = gc.authenticate(username=login, password=password)

        response = gc.get("token/session")

        user = gc.get("user/me")["login"]

        return {"user": user, "token": response["token"]}, True, False, "", ""
    except:
        return (
            {},
            False,
            True,
            no_update,
            no_update,
        )


@callback(
    [
        Output("login-modal", "is_open", allow_duplicate=True),
        Output("login", "value", allow_duplicate=True),
        Output("password", "value", allow_duplicate=True),
        Output("login-failed", "hidden", allow_duplicate=True),
    ],
    Input("close-login-modal", "n_clicks"),
    prevent_initial_call=True,
)
def close_login_modal(n_clicks):
    if n_clicks:
        return False, "", "", True

    return False, "", "", True


@callback(
    [
        Output("user-store", "data", allow_duplicate=True),
        Output("logout-modal", "is_open", allow_duplicate=True),
    ],
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def logout(n_clicks):
    if n_clicks:
        return {}, False

    return no_update, False
