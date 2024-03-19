import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import settings as s

# Assume gc is your Girder Client, you might need to import and configure it properly.

login_state = dcc.Store(id="login-state", data={"logged_in": False, "username": None})


login_modal = dbc.Modal(
    [
        dbc.ModalHeader("Login Notification", className="bg-primary text-white"),
        dbc.ModalBody(
            id="login-notification-body", className="text-center"
        ),  # Message will be set here
        dbc.Input(
            placeholder="Username",
            id="username-input",
            className="my-2 modal-input-height",
            style={"maxWidth": 200},
        ),
        dbc.Input(
            placeholder="Password",
            id="password-input",
            type="password",
            className="mb-3 modal-input-height",
            style={"maxWidth": 200},
        ),
        dbc.Button(
            "Authenticate", id="authenticate-button", color="primary", className="w-100"
        ),
        dbc.ModalFooter(
            dbc.Button(
                "Close",
                id="close-login-modal-btn",
                className="ml-auto",
                color="secondary",
            )
        ),
    ],
    id="login-modal",
    is_open=False,
    centered=True,
    size="lg",
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
                style={"marginRight": "30px"},
            ),
            span=2,
            style={"display": "flex", "justifyContent": "flex-end"},
        ),
    ],
    gutter="xl",
    justify="end",
    style={"height": "30%"},
)

loginSuccess = dmc.Notification(
    title="Login Status",
    id="login-success-notification",
    action="show",
    message="Login was successful",
    icon=DashIconify(icon="ic:round-celebration"),
)

dsa_login_panel = dbc.Container(
    [dsa_login_panel, login_state, loginSuccess],
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
        Input("close-login-modal-btn", "n_clicks"),
    ],
    [
        State("username-input", "value"),
        State("password-input", "value"),
        State("login-state", "data"),
        State("login-modal", "is_open"),
    ],
)
def login_logout(
    n_clicks_login,
    n_clicks_authenticate,
    n_clicks_close,
    username,
    password,
    login_state,
    is_open,
):
    ctx = dash.callback_context
    if not ctx.triggered:
        if s.DSAKEY:
            _ = s.gc.authenticate(apiKey=s.DSAKEY)
            s.DSA_LOGIN_SUCCESS = True
            tokenOwner = s.gc.get("user/me")["login"]
            return (
                {"logged_in": True, "username": tokenOwner},
                "Logout",
                f"Logged in as: {tokenOwner}",
                False,
                "",
            )
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if button_id == "login-logout-button":
        if login_state["logged_in"]:
            return (
                {"logged_in": False, "username": None},
                "Login",
                "Logged out",
                False,
                "",
            )
        return dash.no_update, dash.no_update, dash.no_update, True, ""
    elif button_id == "authenticate-button":
        if username and password:
            _ = s.gc.authenticate(username=username, password=password)
            s.DSA_LOGIN_SUCCESS = True
            return (
                {"logged_in": True, "username": username},
                "Logout",
                f"Logged in as: {username}",
                False,
                "",
            )
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            "Login failed. Please check your credentials.",
        )
    elif button_id == "close-login-modal-btn":
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            not is_open,
            dash.no_update,
        )
    return (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )
