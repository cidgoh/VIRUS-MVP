"""Functions for generating toolbar view."""

import dash_bootstrap_components as dbc
import dash_core_components as dcc


def get_toolbar_row_div():
    """Get Dash Bootstrap Components row that sits above heatmap.

    This contains a col with buttons for selecting and uploading
    strains, a col for displaying dialog to the user, and the clade
    defining mutations switch.

    :return: Dash Bootstrap Component row with upload button and clade
        defining mutations switch.
    :rtype: dbc.Row
    """
    ret = dbc.Row([
        dbc.Col(
            dbc.ButtonGroup([
                get_select_lineages_toolbar_btn(),
                get_file_upload_component()
            ]),
            className="my-auto",
            width={"offset": 1}
        ),
        dbc.Col(
            # Empty on launch; populated after user uploads data
            className="my-auto",
            id="dialog-col"
        ),
        dbc.Col(
            get_clade_defining_mutations_switch_form_group(),
            className="my-auto",
            width={"size": 2}
        )],
        className="mt-3"
    )
    return ret


def get_select_lineages_toolbar_btn():
    """Returns toolbar button for opening select lineages modal.

    :return: Dash Bootstrap Components button with appropriate label
        for selecting lineages.
    :rtype: dbc.Button
    """
    return dbc.Button("Select lineages",
                      id="open-select-lineages-modal-btn",
                      className="mr-1")


def get_select_lineages_modal():
    """Returns select lineages modal.

    This modal is initially closed, and the body is empty.

    :return: Initially closed Dash Bootstrap Components modal for
        selecting lineages.
    :rtype: dbc.Modal
    """
    return dbc.Modal([
        dbc.ModalHeader("Select lineages"),
        # Empty at launch; populated when user opens modal
        dbc.ModalBody(None, id="select-lineages-modal-body"),
        dbc.ModalFooter(get_select_lineages_modal_footer())
    ], id="select-lineages-modal")


def get_select_lineages_modal_body(data):
    """Returns select lineages modal body.

    :param data: ``get_data`` return value
    :type data: dict
    :return: Checkboxes for each directory containing strains, with
        only boxes for non-hidden strains checked.
    :rtype: list[dbc.FormGroup]
    """
    modal_body = []
    for dir_ in reversed(data["dir_strains"]):
        checklist_options = []
        selected_values = []
        for strain in reversed(data["dir_strains"][dir_]):
            checklist_options.append({
                "label": strain,
                "value": strain
            })
            # Strain is not currently hidden
            if strain in data["heatmap_y"]:
                selected_values.append(strain)
        form_group = dbc.FormGroup([
            dbc.Label(dir_),
            dbc.Checklist(
                id={"type": "select-lineages-modal-checklist", "index": dir_},
                options=checklist_options,
                value=selected_values
            )
        ])
        modal_body.append(form_group)
    return modal_body


def get_select_lineages_modal_footer():
    """Returns select lineages modal footer.

    The footer has an ok and and cancel button for confirming and
    cancelling changes respectively for the strains that should be
    hidden in the heatmap.

    :return: Dash Bootstrap Components button group that will go inside
        the select lineages modal footer.
    :rtype: dbc.ButtonGroup
    """
    return dbc.ButtonGroup([
        dbc.Button("Ok",
                   className="mr-1",
                   color="success",
                   id="select-lineages-ok-btn"),
        dbc.Button("Cancel",
                   color="danger",
                   id="select-lineages-cancel-btn"),
    ])


def get_file_upload_component():
    """Get Dash component for upload button.

    :return: Dash upload component with a dash bootstrap button
        component inside.
    :rtype: dcc.Upload
    """
    return dcc.Upload(
        dbc.Button("Upload", color="primary"),
        id="upload-file"
    )


def get_clade_defining_mutations_switch_form_group():
    """Get form group for clade defining mutations switch.

    This is a Dash Bootstrap Components form group.

    :return: Dash Bootstrap Components form group with clade defining
        mutations switch.
    :rtype: dbc.FormGroup
    """
    ret = dbc.FormGroup([
        dbc.Checklist(
            options=[{
                "label": "Clade defining mutations",
                "value": 1
            }],
            value=[],
            id="clade-defining-mutations-switch",
            switch=True
        )],
        className="mb-0"
    )
    return ret
