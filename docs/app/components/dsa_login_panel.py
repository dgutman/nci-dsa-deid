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
        dbc.ModalHeader("Login Notification"),
        dbc.ModalBody(id="login-notification-body"),
        dbc.Input(placeholder="Username", id="username-input"),
        dbc.Input(placeholder="Password", id="password-input", type="password"),
        dbc.Button("Authenticate", id="authenticate-button"),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-login-modal-btn", className="ml-auto")
        ),
    ],
    id="login-modal",
)

dsa_login_panel = dmc.Grid(
    children=[
        dmc.Col(html.H1("NCI DeID Upload Agent"), span=3),
        dmc.Col(
            html.Span(
                [
                    dcc.Store(id="userName", data=None),
                    dmc.Text("Logged out", id="userNameDisplay_text"),
                ]
            ),
            span=3,
        ),
        login_modal,
        dmc.Col(
            dmc.Button(
                "Login", variant="filled", color="red", id="login-logout-button"
            ),
            span=1,
        ),
    ],
    gutter="xl",
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
    ],
    [
        State("username-input", "value"),
        State("password-input", "value"),
        State("login-state", "data"),
    ],
)
def login_logout(
    n_clicks_login, n_clicks_authenticate, username, password, login_state
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
    return (
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
        dash.no_update,
    )


@callback(
    Output("close-login-modal-btn", "n_clicks"),
    [Input("login-modal", "is_open")],
    [State("close-login-modal-btn", "n_clicks")],
)
def reset_close_button(is_open, n_clicks):
    if not is_open:
        return 0
    return n_clicks


# import dash_mantine_components as dmc
# from dash import html, callback, Input, Output, State, callback_context, dcc
# import dash_bootstrap_components as dbc
# import dash
# from settings import gc, DSA_LOGIN_SUCCESS
# from dash_iconify import DashIconify
# import settings as s


# import dash
# import dash_bootstrap_components as dbc
# import dash_mantine_components as dmc
# from dash import dcc, html, callback, Input, Output, State
# from dash_iconify import DashIconify
# import settings as s


# login_state = gc(id="login-state", data={"logged_in": False, "username": None})


# login_modal = dbc.Modal(
#     [
#         dbc.ModalHeader("Login Notification"),
#         dbc.ModalBody(id="login-notification-body"),  # Message will be set here
#         dbc.Input(placeholder="Username", id="username-input"),
#         dbc.Input(placeholder="Password", id="password-input", type="password"),
#         dbc.Button("Authenticate", id="authenticate-button"),
#         dbc.ModalFooter(
#             dbc.Button("Close", id="close-login-modal-btn", className="ml-auto")
#         ),
#     ],
#     id="login-modal",
# )


# from dash.dependencies import MATCH, ALL


# @callback(
#     [
#         Output("login-state", "data"),
#         Output("userNameDisplay_text", "children"),
#         Output("login-logout-button", "children"),
#     ],
#     [
#         Input("app-load-trigger", "data")
#     ],  # Assuming you have a dcc.Store with id "app-load-trigger" that updates when the app loads
# )
# def initialize_login_state(_):
#     gcEY:
#         _ = gc.authenticate(apiKey=s.DSAKEY)
#         s.DSA_LOGIN_SUCCESS = True
#         tokenOwner = gc.get("user/me")["login"]
#         return (
#             {"logged_in": True, "username": tokenOwner},
#             f"Logged in as: {tokenOwner}",
#             "Logout",
#         )
#     return {"logged_in": False, "username": None}, "Logged out", "Login"


# dsa_login_panel = dmc.Grid(
#     children=[
#         dmc.Col(html.H1("NCI DeID Upload Agent"), span=3),
#         dmc.Col(
#             html.Span(
#                 [
#                     dcc.Store(id="userName", data=None),
#                     dmc.Text("Logged out", id="userNameDisplay_text"),
#                 ]
#             ),
#             span=3,
#         ),
#         login_modal,
#         dmc.Col(
#             dmc.Button(
#                 "Login", variant="filled", color="red", id="login-logout-button"
#             ),
#             span=1,
#         ),
#     ],
#     gutter="xl",
# )

# loginSuccess = dmc.Notification(
#     title="Login Status",
#     id="login-success-notification",
#     action="show",
#     message="Login was successful",
#     icon=DashIconify(icon="ic:round-celebration"),
# )

# dsa_login_panel = dbc.Container(
#     [dsa_login_panel, login_state, loginSuccess],
#     fluid=True,
#     style={"padding-top": "20px"},
# )


# @callback(
#     [
#         Output("login-state", "data"),
#         Output("login-logout-button", "children"),
#         Output("userNameDisplay_text", "children"),
#         Output("login-modal", "is_open"),
#         Output("login-notification-body", "children"),
#     ],
#     [
#         Input("login-logout-button", "n_clicks"),
#         Input("authenticate-button", "n_clicks"),
#     ],
#     [
#         State("username-input", "value"),
#         State("password-input", "value"),
#         State("login-state", "data"),
#     ],
# )
# def login_logout(
#     n_clicks_login, n_clicks_authenticate, username, password, login_state
# ):
#     ctx = dash.callback_context

#     if not ctx.triggered:
#         if s.DSAKEY:
#             _ = gc.authenticate(apiKey=s.DSAKEY)
#             # print(_)
#             s.DSA_LOGIN_SUCCESS = True
#             tokenOwner = gc.get("user/me")["login"]
#             return dash.no_update, dash.no_update, loginSuccess, "green", tokenOwner
#         else:
#             return (
#                 dash.no_update,
#                 dash.no_update,
#                 dash.no_update,
#                 dash.no_update,
#                 dash.no_update,
#             )

#     button_id = ctx.triggered[0]["prop_id"].split(".")[0]

#     if button_id == "login-logout-button":
#         if login_state["logged_in"]:
#             # Log out
#             return (
#                 {"logged_in": False, "username": None},
#                 "Login",
#                 "Logged out",
#                 False,
#                 "",
#             )
#         else:
#             return dash.no_update, dash.no_update, dash.no_update, True, ""

#     elif button_id == "authenticate-button":
#         if username and password:
#             # Here goes your login logic
#             # If authentication is successful:
#             return (
#                 {"logged_in": True, "username": username},
#                 "Logout",
#                 f"Logged in as: {username}",
#                 False,
#                 "",
#             )
#             # If login fails:
#             # return dash.no_update, dash.no_update, dash.no_update, dash.no_update, "Login failed. Please check your credentials."

#     return (
#         dash.no_update,
#         dash.no_update,
#         dash.no_update,
#         dash.no_update,
#         dash.no_update,
#     )


# @callback(
#     Output("close-login-modal-btn", "n_clicks"),
#     [Input("login-modal", "is_open")],
#     [State("close-login-modal-btn", "n_clicks")],
# )
# def reset_close_button(is_open, n_clicks):
#     if not is_open:
#         return 0
#     return n_clicks


# ## Make this a global for now so I can track if the dsa is logged in..

# ## TO DO.. ADD LOGOUT BUTTON LOGIC

# login_logout_button = dmc.Col(
#     dmc.Button("Login", id="login-logout-button", variant="filled", color="red"),
#     span=1,
# )


# login_state = dcc.Store(id="login-state", data={"logged_in": False, "username": None})


# @callback(
#     [
#         Output("login-state", "data"),
#         Output("login-logout-button", "children"),
#         Output("userNameDisplay_text", "children"),
#     ],
#     [Input("login-logout-button", "n_clicks")],
#     [
#         State("username-input", "value"),
#         State("password-input", "value"),
#         State("login-state", "data"),
#     ],
# )
# def login_logout(n_clicks, username, password, login_state):
#     if n_clicks:
#         if login_state["logged_in"]:
#             # Log out
#             return {"logged_in": False, "username": None}, "Login", "Logged out"
#         else:
#             # Implement your login logic here
#             # If authentication is successful:
#             return (
#                 {"logged_in": True, "username": username},
#                 "Logout",
#                 f"Logged in as: {username}",
#             )
#             # If login fails, you can return an error message or keep the state unchanged
#     return dash.no_update, dash.no_update, dash.no_update


# login_modal = html.Div(
#     [
#         dbc.Modal(
#             [
#                 dbc.ModalHeader("Login Notification"),
#                 dmc.Col(
#                     [dbc.Input(placeholder="Username", id="username-input")],
#                     span=4,
#                 ),
#                 dmc.Col(
#                     [
#                         # dbc.Label("Password", html_for="password-input"),
#                         dbc.Input(
#                             placeholder="Password", id="password-input", type="password"
#                         ),
#                     ],
#                     span=4,
#                 ),
#                 dbc.ModalBody(id="login-notification-body"),  # Message will be set here
#                 dmc.Col(
#                     dbc.Button(
#                         "Authenticate", id="authenticate-userpass-login", disabled=True
#                     ),
#                     # width=4,
#                 ),
#                 dbc.ModalFooter(
#                     dbc.Button("Close", id="close-login-modal-btn", className="ml-auto")
#                 ),
#             ],
#             id="login-notification-modal",
#         )
#     ]
# )


# ### Create callback to login via supplying  a username and apssword
# @callback(
#     Output("authenticate-userpass-login", "disabled"),
#     Input("username-input", "value"),
#     Input("password-input", "value"),
# )
# def enablePasswordLogin(username, password):
#     ## Disable authenticate button if no user or password supplied...
#     if username and password:
#         return False
#     return True


# @callback(Output("userNameDisplay_text", "children"), Input("userName", "data"))
# def updateLoggedInUserDisplay(userName):
#     return f"Logged in as: {userName}"


# dsa_login_panel = dmc.Grid(
#     children=[
#         dmc.Col(html.H1("NCI DeID Upload Agent"), span=3),
#         login_modal,
#         dmc.Col(
#             html.Span(
#                 [
#                     dcc.Store(id="userName", data=None),
#                     dmc.Text("Logged in as:", id="userNameDisplay_text"),
#                 ]
#             ),
#             span=3,
#         ),
#         dmc.Col(
#             dmc.Button("Login", variant="filled", color="red", id="login-button"),
#             span=1,
#         ),
#     ],
#     gutter="xl",
# )


# loginSuccess = dmc.Notification(
#     title="Login Status",
#     id="simple-notify",
#     action="show",
#     message="Login was successful",
#     icon=DashIconify(icon="ic:round-celebration"),
# )


# @callback(
#     [
#         Output("login-notification-modal", "is_open"),
#         Output("login-notification-body", "children"),
#         Output("notifications-container", "children"),
#         Output("login-button", "color"),
#         Output("userName", "data"),
#     ],
#     Input("login-button", "n_clicks"),
#     Input("close-login-modal-btn", "n_clicks"),
#     Input("authenticate-userpass-login", "n_clicks"),
#     State("username-input", "value"),
#     State("password-input", "value"),
#     State("login-notification-modal", "is_open"),
# )
# def validate_form(
#     login_clicks, close_clicks, manual_login_clicks, username, password, is_open
# ):
#     ctx = callback_context

#     if not ctx.triggered:
#         # No button has been clicked yet, so we return without making any changes
#         ## See if the DSA Token is set
#         if s.DSAKEY:
#             _ = gc.authenticate(apiKey=s.DSAKEY)
#             # print(_)
#             s.DSA_LOGIN_SUCCESS = True

#             return dash.no_update, dash.no_update, loginSuccess, "green", "TBD"

#     button_id = ctx.triggered[0]["prop_id"].split(".")[0]

#     if button_id in ["login-button", "authenticate-userpass-login"]:
#         if not username or not password:
#             return (
#                 True,
#                 "",
#                 dash.no_update,
#                 "red",
#                 "SomeBody",
#             )  # Open modal with error message
#         else:
#             try:
#                 _ = gc.authenticate(username=username, password=password)
#                 s.DSA_LOGIN_SUCCESS = True
#                 ### Add not a modal but a mantine notification instead..
#                 # print(_)
#                 return (dash.no_update, dash.no_update, loginSuccess, "green")
#             except:
#                 return (
#                     True,
#                     "LOGIN FAILED !!! Check your password",
#                     dash.no_update,
#                     "red",
#                     "SombeBody",
#                 )  # Open modal with error message

#         # Continue with the login process if needed
#         # If login is successful:
#         # return True, "Login successful!"
#         # If login fails:
#         # return True, "Login failed. Please check your credentials."

#     elif button_id == "close-login-modal-btn":
#         return (
#             not is_open,
#             "",
#             dash.no_update,
#             dash.no_update,
#             dash.no_update,
#         )  # Toggle modal visibility based on its current state

#     return (
#         dash.no_update,
#         dash.no_update,
#         dash.no_update,
#         dash.no_update,
#         dash.no_update,
#     )


# # This setup toggles the visibility of the modal when the login button is clicked, and it displays the appropriate message based on the input. The modal can be closed using the "Close" button. Adjust the login logic as per your needs.
