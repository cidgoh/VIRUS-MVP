"""Functions for generating histogram view."""

import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
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
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="histogram-rel-pos-bar",
                    style={"backgroundColor": "red", "height": "1vh"}
                ),
                width={"offset": 1, "size": 10}
            )
        )
    ]


def get_histogram_fig(data):
    """Get Plotly figure representing histogram view.

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
    ret.add_trace(get_histogram_main_obj(data), row=1, col=1)
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


def get_histogram_main_obj(data):
    """Get Plotly graph object representing bars in histogram view.

    This is just the bars, without the gene bar.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly graph object representing main plot with bars in
        histogram view.
    :rtype: go.Histogram
    """
    ret = go.Histogram(
        x=[int(x) for x in data["histogram_x"]],
        xbins={"start": 1, "size": 100},
        marker={"color": "black"},
        showlegend=False,
        hovertemplate="%{y} mutations across positions %{x}<extra></extra>"
    )
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
