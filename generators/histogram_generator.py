"""Functions for generating histogram view."""

import math

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from definitions import GENE_COLORS_DICT, GENE_POSITIONS_DICT

def get_histogram_row(data):
    """Get Dash Bootstrap Components row containing histogram view.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components rows containing histogram view
    :rtype: list[dbc.Row]
    """
    return dbc.Row(
        dbc.Col(
            [
                dbc.Row(
                    get_histogram_top_row(data),
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
                    ),
                    no_gutters=True
                )
            ]
        ), no_gutters=True)


def get_histogram_top_row(data):
    """Get the top Dash Bootstrap Components row in the histogram view.

    This consists of the actual histogram, and also a scatter plot
    acting as a mock axis. A mock axis was necessary to get the
    histogram display as intended, and to avoid breaking the histogram
    relative position bar.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Top Dash Bootstrap Components row in the histogram view
    :rtype: dbc.Row
    """
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
    """Get the mock axis figure next to the histogram.

    This is a scatter plot, that uses the max value from the histogram
    to produce a mock y axis.

    :param np_histogram: Numpy histogram object used to produce bars in
        histogram view.
    :type np_histogram: tuple
    :return: Figure containing scatter plot representing mock histogram
        axis.
    :rtype: go.Figure
    """
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
        font={"size": 16},
        xaxis1={"visible": False, "range": [0, 100], "fixedrange": True},
        yaxis1={"visible": False, "range": [0, 100], "fixedrange": True},
    )
    return ret


def get_histogram_fig(np_histogram):
    """Get Plotly figure representing axis-less histogram and gene bar.

    :param np_histogram: Numpy histogram object used to produce bars in
        histogram view.
    :type np_histogram: tuple
    :return: Plotly figure representing histogram view
    :rtype: go.Figure
    """
    ret = make_subplots(rows=2,
                        cols=1,
                        row_heights=[0.7, 0.3],
                        vertical_spacing=0)
    ret.add_trace(get_histogram_graph_obj(np_histogram), row=1, col=1)
    for bar_obj in get_histogram_gene_bar_obj_list():
        ret.add_trace(bar_obj, row=2, col=1)
    ret.update_layout(
        margin={"t": 0, "b": 0, "l": 0, "r": 0, "pad": 0},
        plot_bgcolor="white",
        bargap=0.1,
        font={"size": 16},
        # TODO hardcoding genome length here because I'm lazy
        xaxis1={"visible": False, "range": [1, 29903], "fixedrange": True},
        xaxis2={"visible": False, "range": [1, 29903], "fixedrange": True},
        yaxis1={"visible": False, "fixedrange": True},
        yaxis2={"visible": False, "fixedrange": True},
        barmode="stack"
    )

    return ret


def get_histogram_graph_obj(np_histogram):
    """Get Plotly graph object representing bars in histogram view.

    This is just the axis-less bars, without the gene bar.

    :param np_histogram: Numpy histogram object used to produce bars in
        histogram view.
    :type np_histogram: tuple
    :return: Plotly graph object representing main plot with bars in
        histogram view.
    :rtype: go.Bar
    """
    [counts, bins] = np_histogram
    bin_medians = 0.5 * (bins[:-1] + bins[1:])
    bin_ranges = np.column_stack((bins[:-1], bins[1:]))
    hover_template = \
        "%{y} mutations across positions %{customdata}<extra></extra>"
    # We use the ``Bar`` function instead of ``Histogram`` because we
    # are using the numpy histogram function instead of the one
    # provided by Plotly.
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
    """Get histogram data structure for histogram view.

    We use the histogram function from numpy instead of the histogram
    function of Plotly because it provides details on the histogram
    after it is generated here in the server-side code. Plotly generates
    histograms on the fly in the browser, which provides no data for
    generating a mock axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Numpy histogram object used to produce bars in histogram
        view.
    :rtype: tuple
    """
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
    ret = []
    total_bar_len_so_far = 0
    last_gene_end = 1
    for gene in GENE_POSITIONS_DICT:
        gene_start = GENE_POSITIONS_DICT[gene]["start"]
        gene_end = GENE_POSITIONS_DICT[gene]["end"]
        igr_color = GENE_COLORS_DICT["INTERGENIC"]
        # Intergenic region before this gene--add it
        if gene_start > last_gene_end:
            intergenic_bar_len = gene_start - total_bar_len_so_far
            total_bar_len_so_far += intergenic_bar_len
            intergenic_bar_obj = go.Bar(name="",
                                        x=[intergenic_bar_len],
                                        y=["foo"],
                                        orientation="h",
                                        marker={
                                            "color": igr_color,
                                            "line": {"width": 0}
                                        },
                                        showlegend=False,
                                        hovertemplate="INTERGENIC")
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
                                    marker={
                                        "color": GENE_COLORS_DICT[gene],
                                        "line": {"width": 0}
                                    },
                                    showlegend=False,
                                    hovertemplate=gene)
        ret.append(intragenic_bar_obj)

    return ret
