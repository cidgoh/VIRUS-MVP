"""Functions that return HTML components rendered by Dash.

These functions do not generate the figures inside the HTML components,
they call the functions that generate figures, and organize them into
HTML divs. We are using the dash bootstrap components, so these
functions return divs in grid format.
"""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import heatmap_generator
import table_generator


def get_toolbar_row_div(data):
    """Get Dash Bootstrap Components row that sits above heatmap.

    This contains a col with buttons for showing and uploading strains,
    a col for displaying dialog to the user, and the clade defining
    mutations switch.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Component row with upload button and clade
        defining mutations switch.
    :rtype: dbc.Row
    """
    ret = dbc.Row([
        dbc.Col(
            dbc.ButtonGroup([
                get_show_strains_component(data),
                get_file_upload_component()
            ]),
            className="my-auto",
            width={"offset": 1}
        ),
        dbc.Col(
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


def get_show_strains_component(data):
    """TODO"""
    dropdown_children = []
    # TODO order
    for strain in data["heatmap_y"]:
        dropdown_children.append(dbc.DropdownMenuItem(strain))

    return dbc.DropdownMenu(
        label="Show",
        children=dropdown_children,
        className="mr-1",
        id="show-dropdown-btn"
    )


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


def get_heatmap_row_div(data):
    """Get Dash Bootstrap Components row containing heatmap columns.

    Several columns are necessary to get the heatmap view the way we
    want it.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components row with left, center, and right
        columns producing the overall heatmap view.
    :rtype: dbc.Row
    """
    ret = dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-left-fig",
                    figure=heatmap_generator.get_heatmap_left_fig(data)
                ),
                style={"width": "90vw"}
            ),
            width=1, style={"overflowX": "hidden"}
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-center-fig",
                    figure=heatmap_generator.get_heatmap_center_fig(data),
                    # There is some sort of weirdness that
                    # overrides figure layout autosize=False value
                    # when the heatmap is re-rendered after launch,
                    # through callbacks. I suspect it is some sort
                    # of race condition between Plotly Python
                    # autosize and PlotlyJs responding to window
                    # resizing. See https://bit.ly/3nfRux2 section
                    # on responsiveness. This line fixes it,
                    # somehow.
                    style={"width": len(data["heatmap_x"]) * 25}
                ),
                style={"overflowX": "scroll"}
            ),
            width=10
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-right-fig",
                    figure=heatmap_generator.get_heatmap_right_fig(data)
                ),
                style={"width": "90vw"}, className="ml-3"
            ),
            width=1, style={"overflowX": "hidden"}
        ),
    ], no_gutters=True, className="mt-3")
    return ret


def get_table_row_div(data):
    """Get Dash Bootstrap Components row containing table view.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components row containing table
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        dbc.Col(
            dcc.Graph(
                id="table",
                figure=
                table_generator.get_table_fig(data, data["heatmap_y"][0])
            )
        ),
    )
    return ret
