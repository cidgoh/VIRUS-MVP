"""TODO"""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go


def get_histogram_row_div(data):
    """TODO"""
    return dbc.Row(
        dbc.Col(
            dcc.Graph(
                id="table",
                figure=get_histogram_fig(),
                config={"displayModeBar": False},
                style={"height": "10vh"}
            ),
        ),
        className="mt-2"
    )


def get_histogram_fig():
    """TODO"""
    ret = go.Figure(
        get_histogram_obj(),
        layout=go.Layout(
            margin={"t": 0, "b": 0, "pad": 0},
            plot_bgcolor="white"
        )
    )
    return ret


def get_histogram_obj():
    """TODO"""
    x = ["1", "2", "2", "3", "3", "3"]
    ret = go.Histogram(
        x=x,
        nbinsx=29903,
        marker={"color": "black"}
    )
    return ret
