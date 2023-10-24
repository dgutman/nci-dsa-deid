import dash_mantine_components as dmc
from dash import html, callback, Input, Output, State, callback_context, dcc
import dash_bootstrap_components as dbc
import dash
from settings import gc, DSA_LOGIN_SUCCESS
from dash_iconify import DashIconify
import settings as s

## Make this a global for now so I can track if the dsa is logged in..

## TO DO.. ADD LOGOUT BUTTON LOGIC

login_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("Login Notification"),
                dmc.Col(
                    [dbc.Input(placeholder="Username", id="username-input")],
                    span=4,
                ),
                dmc.Col(
                    [
                        # dbc.Label("Password", html_for="password-input"),
                        dbc.Input(
                            placeholder="Password", id="password-input", type="password"
                        ),
                    ],
                    span=4,
                ),
                dbc.ModalBody(id="login-notification-body"),  # Message will be set here
                dmc.Col(
                    dbc.Button(
                        "Authenticate", id="authenticate-userpass-login", disabled=True
                    ),
                    # width=4,
                ),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-login-modal-btn", className="ml-auto")
                ),
            ],
            id="login-notification-modal",
        )
    ]
)


### Create callback to login via supplying  a username and apssword
@callback(
    Output("authenticate-userpass-login", "disabled"),
    Input("username-input", "value"),
    Input("password-input", "value"),
)
def enablePasswordLogin(username, password):
    ## Disable authenticate button if no user or password supplied...
    if username and password:
        return False
    return True


dsa_login_panel = dmc.Grid(
    children=[
        dmc.Col(html.H1("NCI DeID Upload Agent"), span=3),
        login_modal,
        dmc.Col(
            html.Span(
                [
                    dcc.Store(id="userName", data=None),
                    dmc.Text("Logged in as:", id="userNameDisplay_text"),
                ]
            ),
            span=3,
        ),
        dmc.Col(
            dmc.Button("Login", variant="filled", color="red", id="login-button"),
            span=1,
        ),
    ],
    gutter="xl",
)


loginSuccess = dmc.Notification(
    title="Login Status",
    id="simple-notify",
    action="show",
    message="Login was successful",
    icon=DashIconify(icon="ic:round-celebration"),
)


@callback(
    [
        Output("login-notification-modal", "is_open"),
        Output("login-notification-body", "children"),
        Output("notifications-container", "children"),
        Output("login-button", "color"),
    ],
    Input("login-button", "n_clicks"),
    Input("close-login-modal-btn", "n_clicks"),
    Input("authenticate-userpass-login", "n_clicks"),
    State("username-input", "value"),
    State("password-input", "value"),
    State("login-notification-modal", "is_open"),
)
def validate_form(
    login_clicks, close_clicks, manual_login_clicks, username, password, is_open
):
    ctx = callback_context

    if not ctx.triggered:
        # No button has been clicked yet, so we return without making any changes
        ## See if the DSA Token is set
        if s.DSAKEY:
            _ = gc.authenticate(apiKey=s.DSAKEY)
            print(_)
            s.DSA_LOGIN_SUCCESS = True

            return dash.no_update, dash.no_update, loginSuccess, "green"

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id in ["login-button", "authenticate-userpass-login"]:
        if not username or not password:
            return (
                True,
                "",
                dash.no_update,
                "red",
            )  # Open modal with error message
        else:
            try:
                _ = gc.authenticate(username=username, password=password)
                s.DSA_LOGIN_SUCCESS = True
                ### Add not a modal but a mantine notification instead..
                print(_)
                return (dash.no_update, dash.no_update, loginSuccess, "green")
            except:
                return (
                    True,
                    "LOGIN FAILED !!! Check your password",
                    dash.no_update,
                    "red",
                )  # Open modal with error message

        # Continue with the login process if needed
        # If login is successful:
        # return True, "Login successful!"
        # If login fails:
        # return True, "Login failed. Please check your credentials."

    elif button_id == "close-login-modal-btn":
        return (
            not is_open,
            "",
            dash.no_update,
            dash.no_update,
        )  # Toggle modal visibility based on its current state

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # if login_clicks:
    #     if not username or not password:
    #         return True, "Both fields are required!"  # Open modal with error message
    #     # Continue with the login process if needed
    #     # If login is successful:
    #     # return True, "Login successful!"
    #     # If login fails:
    #     # return True, "Login failed. Please check your credentials."
    # return not is_open, ""  # Toggle modal visibility based on its current state


# This setup toggles the visibility of the modal when the login button is clicked, and it displays the appropriate message based on the input. The modal can be closed using the "Close" button. Adjust the login logic as per your needs.
