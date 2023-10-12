# components/modals.py

import dash_bootstrap_components as dbc
from .trees import tree_layout

modal_tree = dbc.Container(
    [
        dbc.Modal(
            [
                dbc.ModalHeader("Select Folder For DeID"),
                dbc.ModalBody(tree_layout),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-modal-btn", className="ml-auto")
                ),
            ],
            id="selectDSAfolder-modal",
        ),
    ]
)
