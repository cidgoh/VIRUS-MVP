"""TODO"""

import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_histogram_row_div(data):
    """TODO"""
    return dbc.Row(
        dbc.Col(
            dcc.Graph(
                id="histogram",
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
    for bar_obj in get_histogram_gene_bar_obj_list():
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
        showlegend=False,
        hovertemplate="%{y} mutations across positions %{x}<extra></extra>"
    )
    return ret


def get_histogram_gene_bar_obj_list():
    """TODO"""
    with open("gene_positions.json") as fp:
        gene_positions_dict = json.load(fp)
    with open("gene_colors.json") as fp:
        gene_colors_dict = json.load(fp)

    ret = []
    total_bar_len_so_far = 0
    for gene in gene_positions_dict:
        this_bar_len = gene_positions_dict[gene]["end"] - total_bar_len_so_far
        total_bar_len_so_far += this_bar_len
        bar_obj = go.Bar(name=gene,
                         x=[this_bar_len],
                         y=["foo"],
                         orientation="h",
                         text=[gene] if this_bar_len > 1000 else [],
                         textposition="inside",
                         insidetextanchor="middle",
                         insidetextfont={"color": "white"},
                         marker={"color": gene_colors_dict[gene]},
                         showlegend=False,
                         hovertemplate=gene
                         )
        ret.append(bar_obj)

    return ret
