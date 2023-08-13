# schema_layout = dbc.Card(
#     [
#         daq.ToggleSwitch(id="my-toggle-switch", value=False),
#         dbc.CardBody(id="schema-output"),
#     ],
#     style={"width": "18rem"},
# )

# @app.callback(Output("schema-output", "children"), [Input("my-toggle-switch", "value")])
# def display_output(value):
#     if value:
#         data = {"a": 1, "b": [1, 2, 3, {"c": 4}]}
#         theme = {
#             "scheme": "monokai",
#             "author": "wimer hazenberg (http://www.monokai.nl)",
#             "base00": "#272822",
#             "base01": "#383830",
#             "base02": "#49483e",
#             "base03": "#75715e",
#             "base04": "#a59f85",
#             "base05": "#f8f8f2",
#             "base06": "#f5f4f1",
#             "base07": "#f9f8f5",
#             "base08": "#f92672",
#             "base09": "#fd971f",
#             "base0A": "#f4bf75",
#             "base0B": "#a6e22e",
#             "base0C": "#a1efe4",
#             "base0D": "#66d9ef",
#             "base0E": "#ae81ff",
#             "base0F": "#cc6633",
#         }
#         return dash_renderjson.DashRenderjson(
#             id="input", data=schema, max_depth=-1, theme=theme, invert_theme=True
#         )

# dbc.Button("Toggle Panel", id="toggle-panel-btn"),
#         html.Div("This is a floating panel", id="floating-panel"),

# @app.callback(
#     Output("floating-panel", "style"),
#     [Input("toggle-panel-btn", "n_clicks")],
#     [State("floating-panel", "style")],
# )
# def toggle_floating_panel(n_clicks, current_style):
#     if not n_clicks:
#         # Default state (can be set to display or not as per your preference)
#         return {"display": "none"}

#     # Toggle display based on current state
#     if current_style and current_style.get("display") == "none":
#         return {"display": "block"}
#     else:
#         return {"display": "none"}
