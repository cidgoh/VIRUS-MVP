"""Functions for generating histogram view."""

import json
import math

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_histogram_row_divs(data):
    """Get Dash Bootstrap Components rows containing histogram view.
    TODO

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components row containing histogram
    :rtype: dbc.Row
    """
    return [
        dbc.Row(
            get_histogram_top_row_div(data),
            id="histogram-top-row-div",
            className="mt-3",
            no_gutters=True
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="histogram-rel-pos-bar",
                    # Margins will be added dynamically clientside
                    style={"backgroundColor": "black", "height": "1vh"}
                ),
                width={"offset": 1, "size": 10}
            )
        )
    ]


def get_histogram_top_row_div(data):
    """TODO"""
    np_histogram = get_np_histogram(data)
    ret = [
        dbc.Col(
            dcc.Graph(
                figure=get_histogram_mock_axis(np_histogram),
                config={"displayModeBar": False},
                style={"height": "7rem"}
            ),
            width={"size": 1}
        ),
        dbc.Col(
            dcc.Graph(
                    id="histogram",
                    figure=get_histogram_fig(np_histogram),
                    config={"displayModeBar": False},
                    style={"height": "7rem"}
            ),
            width={"size": 10}
        ),
    ]
    return ret


def get_histogram_mock_axis(np_histogram):
    """TODO"""
    ret = make_subplots(rows=2,
                        cols=1,
                        row_heights=[0.7, 0.3],
                        vertical_spacing=0)
    counts = np_histogram[0]
    mock_obj = go.Scatter(
        x=[95, 95],
        y=[0, 100],
        mode="lines+text",
        line={"color": "black"},
        text=["0 ", "%s " % counts.max()],
        textposition=["top left", "bottom left"],
        hoverinfo="skip"
    )
    ret.add_trace(mock_obj, row=1, col=1)
    ret.update_layout(
        margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
        plot_bgcolor="white",
        font={"size": 18},
        xaxis1={"visible": False, "range": [0, 100], "fixedrange": True},
        yaxis1={"visible": False, "range": [0, 100], "fixedrange": True},
    )
    return ret


def get_histogram_fig(np_histogram):
    """Get Plotly figure representing histogram view.TODO

    This figure has two subplots. One for the main histogram, and the
    other for corresponding the gene bar.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure representing histogram view
    :rtype: go.Figure
    """
    ret = make_subplots(rows=2,
                        cols=1,
                        row_heights=[0.7, 0.3],
                        vertical_spacing=0)
    ret.add_trace(get_histogram_main_obj(np_histogram), row=1, col=1)
    for bar_obj in get_histogram_gene_bar_obj_list():
        ret.add_trace(bar_obj, row=2, col=1)
    ret.update_layout(
        margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
        plot_bgcolor="white",
        bargap=0.1,
        font={"size": 18},
        xaxis1={"visible": False, "range": [1, 29903], "fixedrange": True},
        xaxis2={"visible": False, "range": [1, 29903], "fixedrange": True},
        yaxis1={"visible": False, "fixedrange": True},
        yaxis2={"visible": False, "fixedrange": True},
        barmode="stack"
    )

    return ret


def get_histogram_main_obj(np_histogram):
    """Get Plotly graph object representing bars in histogram view.
    TODO

    This is just the bars, without the gene bar.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly graph object representing main plot with bars in
        histogram view.
    :rtype: go.Histogram
    """
    [counts, bins] = np_histogram
    bin_medians = 0.5 * (bins[:-1] + bins[1:])
    bin_ranges = np.column_stack((bins[:-1], bins[1:]))
    hover_template = \
        "%{y} mutations across positions %{customdata}<extra></extra>"
    ret = go.Bar(
        x=bin_medians,
        y=counts,
        marker={"color": "black"},
        showlegend=False,
        customdata=["%s to %s" % (x[0], x[1]) for x in bin_ranges],
        hovertemplate=hover_template
    )
    return ret


def get_np_histogram(data):
    """TODO"""
    np_input = [int(x) for x in data["histogram_x"]]
    np_last_bin = int(math.ceil(max(np_input) / 100)) * 100
    ret = np.histogram(np_input, bins=range(0, np_last_bin+1, 100))
    return ret


def get_histogram_gene_bar_obj_list():
    """Get Plotly graph object list representing histogram gene bar.

    We return a list so they can be stacked on top of each other in
    ``get_histogram_fig``.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: List of plotly graph objects representing gene bar in
        histogram view.
    :rtype: list[go.Bar]
    """
    with open("gene_positions.json") as fp:
        gene_positions_dict = json.load(fp)
    with open("gene_colors.json") as fp:
        gene_colors_dict = json.load(fp)

    ret = []
    total_bar_len_so_far = 0
    last_gene_end = 1
    for gene in gene_positions_dict:
        gene_start = gene_positions_dict[gene]["start"]
        gene_end = gene_positions_dict[gene]["end"]
        # Intergenic region before this gene--add it
        if gene_start > last_gene_end:
            intergenic_bar_len = gene_start - total_bar_len_so_far
            total_bar_len_so_far += intergenic_bar_len
            intergenic_bar_obj = go.Bar(name="",
                                        x=[intergenic_bar_len],
                                        y=["foo"],
                                        orientation="h",
                                        marker={"color": "white"},
                                        showlegend=False,
                                        hoverinfo="skip")
            ret.append(intergenic_bar_obj)
        # Now add intragenic bar
        intragenic_bar_len = gene_end - total_bar_len_so_far
        total_bar_len_so_far += intragenic_bar_len
        intragenic_bar_text = [gene] if intragenic_bar_len > 1000 else []
        intragenic_bar_obj = go.Bar(name=gene,
                                    x=[intragenic_bar_len],
                                    y=["foo"],
                                    orientation="h",
                                    text=intragenic_bar_text,
                                    textposition="inside",
                                    insidetextanchor="middle",
                                    insidetextfont={"color": "white"},
                                    marker={"color": gene_colors_dict[gene]},
                                    showlegend=False,
                                    hovertemplate=gene)
        ret.append(intragenic_bar_obj)

    return ret
