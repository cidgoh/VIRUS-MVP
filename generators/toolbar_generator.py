"""Functions for generating toolbar view."""

import os

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html


def get_toolbar_row(data):
    """Get Dash Bootstrap Components row that sits above heatmap.

    This contains a col with buttons for selecting and uploading
    strains, a col for displaying dialog to the user, and the clade
    defining mutations switch.

    :param data: ``get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Component row with upload button and clade
        defining mutations switch.
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        [
            dbc.Col(
                dbc.ButtonGroup(
                    [
                        get_select_lineages_toolbar_btn(),
                        get_file_upload_component(),
                        get_file_download_component()
                    ],
                    className="pl-4 pl-xl-5"
                ),
                width=4
            ),
            dbc.Col(
                # Empty on launch
                className="my-auto",
                id="dialog-col"
            ),
            dbc.Col(
                get_mutation_freq_slider(data),
                className="my-auto",
                id="mutation-freq-slider-col",
                width=2
            ),
            dbc.Col(
                get_clade_defining_mutations_switch_form_group(),
                className="my-auto pl-xl-5",
                width=2
            ),
            get_select_lineages_modal()
        ],
        className="mt-3 ml-xl-3"
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
        dbc.ModalBody(None,
                      id="select-lineages-modal-body",
                      style={"height": "50vh", "overflowY": "scroll"}),
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
            if strain not in data["hidden_strains"]:
                selected_values.append(strain)
        form_group = dbc.FormGroup([
            dbc.Label(os.path.basename(dir_)),
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
    icon = html.I(className="bi-cloud-upload-fill", style={"font-size": 18})
    return dcc.Upload(
        dbc.Button(icon, color="success", outline=True),
        id="upload-file",
        className="mr-1"
    )


def get_file_download_component():
    """Get dash component for download button.

    :return: Dash html div with button and download component inside.
    :rtype: html.Div
    """
    icon = html.I(className="bi-cloud-download-fill", style={"font-size": 18})
    return html.Div([
        dbc.Button(icon, color="primary", outline=True),
        dcc.Download(id="download-file")
    ])


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

        if num_val < min_val:
            min_val = num_val
        if num_val > max_val:
            max_val = num_val
        marks[num_val] = {
            "label": str_val,
            "style": {"display": "none"}
        }
    marks[min_val]["style"].pop("display")
    marks[min_val]["label"] = "Freq=" + marks[min_val]["label"]
    marks[max_val]["style"].pop("display")
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
    :rtype: dbc.FormGroup
    """
    ret = dbc.FormGroup([
        dbc.Checklist(
            options=[{
                "label": "Clade defining",
                "value": 1
            }],
            value=[],
            id="clade-defining-mutations-switch",
            switch=True
        )],
        className="mb-0 pl-xl-2"
    )
    return ret
