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
                figure=get_histogram_fig(data),
                config={"displayModeBar": False},
                style={"height": "7rem"}
            ),
            width={"offset": 1, "size": 10}
        ),
        className="mt-2"
    )


def get_histogram_fig(data):
    """TODO"""
    ret = go.Figure(
        get_histogram_obj(data),
        layout=go.Layout(
            margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
            plot_bgcolor="white",
            bargap=0.1,
            font={"size": 18}
        )
    )
    return ret


def get_histogram_obj(data):
    """TODO"""
    ret = go.Histogram(
        x=[int(x) for x in data["histogram_x"]],
        xbins={
            "start": 0,
            "size": 100
        },
        marker={
            "color": "black"
        }
    )
    return ret
