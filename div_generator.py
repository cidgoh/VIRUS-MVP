"""TODO..."""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import heatmap_generator
import table_generator


def get_clade_defining_mutations_switch():
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
                width={
                    "size": 2
                }
            ),
            justify="end",
            className="mt-3"
        )
    ])
    return ret


def get_heatmap_row_div(data):
    """TODO..."""
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
                    style={"width": "90vw"}
                ),
                width=1, style={"overflowX": "hidden"}
            ),
        ], no_gutters=True, className="mt-3"),
    ])
    return ret


def get_table_row_div(data):
    """TODO..."""
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
