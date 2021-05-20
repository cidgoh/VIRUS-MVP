"""TODO"""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots


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
    ret = make_subplots(rows=2,
                        cols=1,
                        row_heights=[0.7, 0.3],
                        vertical_spacing=0)
    ret.add_trace(get_histogram_main_obj(data), row=1, col=1)
    for bar_obj in get_histogram_gene_bar_obj(data):
        ret.add_trace(bar_obj, row=2, col=1)
    ret.update_layout(
        margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
        plot_bgcolor="white",
        bargap=0.1,
        font={"size": 18},
        xaxis1={"visible": False, "range": [1, 29903]},
        xaxis2={"visible": False, "range": [1, 29903]},
        yaxis1={"visible": False},
        yaxis2={"visible": False},
        barmode="stack"
    )

    return ret


def get_histogram_main_obj(data):
    """TODO"""
    ret = go.Histogram(
        x=[int(x) for x in data["histogram_x"]],
        xbins={"start": 1, "size": 100},
        marker={"color": "black"},
        showlegend=False
    )
    return ret


def get_histogram_gene_bar_obj(data):
    """TODO"""
    ret = [
        go.Bar(name='SF Zoo',
               x=[1000],
               y=["foo"],
               orientation="h",
               text=["ham"],
               textposition="inside",
               insidetextanchor="middle",
               insidetextfont={"color": "white"},
               marker={"color": "red"},
               showlegend=False),
        go.Bar(name='LA Zoo',
               x=[28903],
               y=["foo"],
               orientation="h",
               text=["spam"],
               textposition="inside",
               insidetextanchor="middle",
               insidetextfont={"color": "white"},
               marker={"color": "blue"},
               showlegend=False),
    ]
    return ret
