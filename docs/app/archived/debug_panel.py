# debug_buttons = html.Div(
#     [
#         dbc.Button(
#             "Get DeidFiles",
#             id="load-files-for-deid-button",
#             color="info",
#         ),
#         dbc.Button(
#             "Load Test Data",
#             id="load-test-data-button",
#         ),
#         dbc.Button("Log Something", id="log-button"),
#         dbc.Row(
#             dbc.Card(
#                 dbc.CardBody(
#                     [
#                         html.P("Error and Status Logs", className="card-text"),
#                         html.Div(
#                             id="log-output",
#                             style={
#                                 "height": "300px",
#                                 "overflow": "auto",
#                                 "border": "1px solid black",
#                             },  # Scrollable styles
#                         ),
#                     ]
#                 ),
#                 className="mt-3",
#             )
#         ),
#     ]
# )

# @app.callback(
#     Output("log-output", "children"),
#     Input("log-interval", "n_intervals"),
#     Input("log-button", "n_clicks"),
#     prevent_initial_call=True,
# )
# def update_log(n, clicks):
#     # This captures the current log content

#     with open(s.logger.handlers[0].baseFilename, "r") as f:
#         log_content = f.read()
#     ## In this case the n refers to the internal not the clicks..
#     # Check which input triggered the callback
#     ctx = dash.callback_context
#     if ctx.triggered[0]["prop_id"] == "log-button.n_clicks":
#         s.logger.info("Button was clicked! %d " % clicks)

#     return html.Pre(log_content)

global log_updated

log_updated = False
