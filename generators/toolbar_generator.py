"""Functions for generating toolbar view."""

import os

from dash import dcc, html
import dash_bootstrap_components as dbc

from definitions import REFERENCE_DATA_DIR


def get_toolbar_row(data):
    """Get Dash Bootstrap Components row that contains toolbar.

    :param data: ``get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Component row with toolbar btns.
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        [
            dbc.Col(
                dbc.ButtonGroup(
                    [
                        get_select_lineages_toolbar_btn(),
                        # This loading displays during user uploads
                        dcc.Loading(
                            get_file_upload_component(),
                            id="upload-loading",
                            type="circle"
                        ),
                        get_file_download_component(),
                        get_jump_to_btn(),
                        get_legend_toggle_component()
                    ],
                    className="ps-4 ps-xl-5"
                ),
                width=7
            ),
            dbc.Col(
                [
                    dcc.Loading(
                        None,
                        id="data-loading",
                        style={"height": "100%", "width": "100%", "margin": 0},
                        type="dot"
                    ),
                    dcc.Loading(
                        None,
                        id="select-lineages-modal-loading",
                        style={"height": "100%", "width": "100%", "margin": 0},
                        type="dot"
                    )
                ],
                id="loading-col",
                width=1
            ),
            dbc.Col(
                get_mutation_freq_slider(data),
                className="my-auto",
                id="mutation-freq-slider-col",
                width=2
            ),
            dbc.Col(
                get_clade_defining_mutations_switch_form_group(),
                className="my-auto ps-xl-5",
                width=2
            ),
            get_select_lineages_modal(data),
            get_confirm_strain_del_modal(),
            get_jump_to_modal()
        ],
        className="mt-3 ms-xl-3"
    )
    return ret


def get_select_lineages_toolbar_btn():
    """Returns toolbar button for opening select lineages modal.

    :return: Dash Bootstrap Components button with appropriate label
        for selecting lineages.
    :rtype: dbc.Button
    """
    return dbc.Button("Select groups",
                      id="open-select-lineages-modal-btn",
                      className="me-2",
                      color="secondary")


def get_select_lineages_modal(data):
    """Returns select lineages modal.

    This modal is initially closed.

    :param data: ``get_data`` return value
    :type data: dict
    :return: Initially closed Dash Bootstrap Components modal for
        selecting lineages.
    :rtype: dbc.Modal
    """
    return dbc.Modal([
        dbc.ModalHeader("Select sample groups"),
        # Empty at launch; populated when user opens modal
        dbc.ModalBody(get_select_lineages_modal_body(data),
                      id="select-lineages-modal-body",
                      style={"height": "50vh", "overflowY": "scroll"}),
        dbc.ModalFooter(get_select_lineages_modal_footer())
    ], id="select-lineages-modal")


def get_select_lineages_modal_body(data):
    """Returns select lineages modal body.

    :param data: ``get_data`` return value
    :type data: dict
    :return: Checkboxes for each directory containing strains, with
        only boxes for non-hidden strains checked, and btns for
        selecting or deselecting all checkboxes.
    :rtype: list
    """
    modal_body = []
    for dir_ in reversed(data["dir_strains_dict"]):
        title = dbc.Row(dbc.Col(os.path.basename(dir_)))

        all_none_btns = dbc.ButtonGroup([
                dbc.Button(
                    "All",
                    size="sm",
                    color="success",
                    id={"type": "select-lineages-modal-all-btn",
                        "index": dir_}
                ),
                dbc.Button(
                    "None",
                    size="sm",
                    color="danger",
                    id={"type": "select-lineages-modal-none-btn",
                        "index": dir_}
                )
            ])

        checkboxes = []
        for strain in data["dir_strains_dict"][dir_]:
            checked = strain not in data["hidden_strains"]
            checkbox = dbc.Checkbox(
                id={"type": "select-lineages-modal-checkbox", "index": strain},
                value=checked
            )
            cols = [
                dbc.Col(checkbox, width=1),
                dbc.Col(strain)
            ]
            if dir_ != REFERENCE_DATA_DIR:
                cols.append(
                    dbc.Col(
                        dbc.Badge("Delete",
                                  id={"type": "checkbox-del-btn",
                                      "index": strain},
                                  color="danger",
                                  style={"cursor": "pointer"}),
                        width=2
                    )
                )
            checkboxes.append(
                dbc.Row(cols)
            )
        checkboxes_div = html.Div(
            checkboxes,
            id={"type": "select-lineages-modal-checklist", "index": dir_}
        )

        modal_body.append(title)
        modal_body.append(all_none_btns)
        modal_body.append(checkboxes_div)

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
                   className="me-1",
                   color="success",
                   id="select-lineages-ok-btn"),
        dbc.Button("Cancel",
                   color="danger",
                   id="select-lineages-cancel-btn"),
    ])


def get_confirm_strain_del_modal():
    """Returns confirm strain deletion modal.

    This modal is initially closed, and the body is empty.

    :return: Initially closed Dash Bootstrap Components modal for
        confirming deletion of strain.
    :rtype: dbc.Modal
    """
    return dbc.Modal([
        dbc.ModalHeader("Are you sure?"),
        # Empty at launch; populated when user opens modal
        dbc.ModalBody(None,
                      id="confirm-strain-del-modal-body"),
        dbc.ModalFooter([
            dbc.Button("Delete",
                       color="danger",
                       id="confirm-strain-del-modal-ok-btn"),
            dbc.Button("Cancel",
                       id="confirm-strain-del-modal-cancel-btn")
        ])
    ], id="confirm-strain-del-modal", size="sm")


def get_file_upload_component():
    """Get Dash component for upload button.

    :return: Dash upload component with a dash bootstrap button
        component inside.
    :rtype: dcc.Upload
    """
    icon = html.I(className="bi-cloud-upload-fill", style={"font-size": 16})
    return dcc.Upload(
        dbc.Button(icon, color="success", outline=True),
        id="upload-file",
        className="me-1"
    )


def get_file_download_component():
    """Get dash component for download button.

    :return: Dash html div with button and download component inside.
    :rtype: html.Div
    """
    icon = html.I(className="bi-cloud-download-fill", style={"font-size": 16})
    return html.Div([
        dbc.Button(icon,
                   color="primary",
                   outline=True,
                   id="download-file-btn"),
        dcc.Download(id="download-file-data"),
    ], className="me-2")


def get_jump_to_btn():
    """Returns button for opening modal for jumping to mutations.

    :return: Dash Bootstrap Components button with appropriate label
        for jumping to mutations.
    :rtype: dbc.Button
    """
    return dbc.Button("Jump to...",
                      color="secondary",
                      outline=True,
                      id="jump-to-btn",
                      className="me-2")


def get_jump_to_modal():
    """Returns modal for jumping to mutations.

    This modal is initially closed, and the body is empty.

    :return: Initially closed Dash Bootstrap Components modal for
        jumping to mutations.
    :rtype: dbc.Modal
    """
    return dbc.Modal([
        dbc.ModalHeader("Jump to mutation"),
        dbc.ModalBody(
            dbc.Row(
                dbc.Col(
                    dcc.Dropdown(
                        id="jump-to-modal-dropdown-search",
                        # Populate when opening modal
                        options=[]
                    )
                )
            ),
            id="jump-to-modal-body"
        ),
        dbc.ModalFooter(
            dbc.ButtonGroup([
                dbc.Button("Cancel",
                           className="me-1",
                           color="secondary",
                           id="jump-to-modal-cancel-btn"),
                dbc.Button("Jump",
                           color="primary",
                           id="jump-to-modal-ok-btn")
            ])
        )
    ], id="jump-to-modal")


def get_legend_toggle_component():
    """Get dash component for toggling heatmap legend.

    :return: Dash Bootstrap Components button with appropriate label
    :rtype: dbc.Button
    """
    return dbc.Button("HELP",
                      color="info",
                      id="toggle-legend-btn")


def get_mutation_freq_slider(data):
    """Return mutation freq slider div.

    :param data: ``get_data`` return value
    :type data: dict
    :return: Mutation freq slider div with marks corresponding to
        unique mutation frequencies in ``data``, and with handles at
        the minimum and maximum positions.
    :rtype: dcc.RangeSlider
    """
    marks = {}
    min_val = 1
    max_val = 0
    for str_val in data["mutation_freq_slider_vals"]:
        # Dash sliders currently have a bug that prevents typing whole
        # numbers as floats. See https://bit.ly/3wgwh9p.
        num_val = float(str_val)
        if num_val % 1 == 0:
            num_val = int(num_val)

        if num_val <= min_val:
            min_val = num_val
        if num_val >= max_val:
            max_val = num_val
        marks[num_val] = {
            "label": str_val,
            "style": {"display": "none"}
        }
    marks[min_val]["label"] = "Freq=" + marks[min_val]["label"]
    if len(marks) > 1:
        marks[min_val]["style"].pop("display")
        marks[max_val]["style"].pop("display")
    else:
        marks[min_val]["style"].pop("display")
    return dcc.RangeSlider(id="mutation-freq-slider",
                           className="p-0",
                           min=min_val,
                           max=max_val,
                           step=None,
                           value=[min_val, max_val],
                           allowCross=False,
                           marks=marks,
                           tooltip={})


def get_clade_defining_mutations_switch_form_group():
    """Get form group for clade defining mutations switch.

    This is a Dash Bootstrap Components form group.

    :return: Dash Bootstrap Components form group with clade defining
        mutations switch.
    :rtype: dbc.Row
    """
    ret = dbc.Row(dbc.Col([
        dbc.Checklist(
            options=[{
                "label": "Clade defining",
                "value": 1
            }],
            value=[],
            id="clade-defining-mutations-switch",
            switch=True
        )],
        className="mb-0 ps-xl-2"
    ))
    return ret
