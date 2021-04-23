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


def get_toolbar_row_div():
    """Get Dash HTML component that sits above heatmap.

    This contains the upload file button, and the clade defining
    mutations switch.

    :return: Dash HTML component with upload button and clade defining
        mutations switch.
    :rtype: html.Div
    """
    ret = html.Div([])
    return ret


def get_clade_defining_mutations_switch():
    """Get Dash HTML component for clade defining mutations switch.

    :return: Dash HTML component with toggle watched by
        ``on_form_change``.
    :rtype: html.Div
    """
    ret = html.Div([
        dbc.Row(
            dbc.Col(
                dbc.FormGroup([
                    dbc.Checklist(
                        options=[{
                            "label": "Clade defining mutations",
                            "value": 1
                        }],
                        value=[],
                        id="clade-defining-mutations-switch",
                        switch=True
                    )
                ]),
                width=2
            ),
            justify="end",
            className="mt-3"
        )
    ])
    return ret


def get_heatmap_row_div(data):
    """Get Dash HTML component containing heatmap view.

    This HTML component is a row of several subcomponents, to get the
    necessary heatmap view.

    :return: Dash HTML component with left, center, and right
        components producing the overall heatmap view.
    :rtype: html.Div
    """
    ret = html.Div([
        dbc.Row([
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
                        figure=heatmap_generator.get_heatmap_center_fig(data)
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
        ], no_gutters=True, className="mt-3"),
    ])
    return ret


def get_table_row_div(data):
    """Get Dash HTML component containing table view.

    :return: Dash HTML component containing table
    :rtype: html.Div
    """
    ret = html.Div([
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id="table",
                    figure=
                    table_generator.get_table_fig(data, data["heatmap_y"][0])
                )
            ),
        )
    ])
    return ret
