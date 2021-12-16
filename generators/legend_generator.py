"""Functions for generating legend view."""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go


def get_legend_collapse():
    """Get Dash Bootstrap Components collapse containing legend row.

    :return: Dash Bootstrap Components collapsable div containing
        legend view.
    :rtype: dbc.Collapse
    """
    ret = dbc.Collapse(
        get_legend_row(),
        id="legend-collapse",
        is_open=False
    )
    return ret


def get_legend_row():
    """Get Dash Bootstrap Components row containing legend columns.

    :return: Dash Bootstrap Components row with multiple cols for
        legend view.
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        [
            dbc.Col(
                dcc.Graph(
                    id="voc-voi-legend-fig",
                    figure=get_voc_voi_legend_fig(),
                    config={"displayModeBar": False},
                ),
                className="border-left border-right border-top border-bottom "
                          "border-dark",
                width={"offset": 1, "size": 1}
            ),
            dbc.Col(
                dcc.Graph(
                    id="single-genome-legend-fig",
                    figure=get_single_genome_legend_fig(),
                    config={"displayModeBar": False},
                ),
                className="border-top border-bottom border-dark",
                width=1
            ),
            dbc.Col(
                dcc.Graph(
                    id="indel-legend-fig",
                    figure=get_indel_legend_fig(),
                    config={"displayModeBar": False},
                ),
                className="border-top border-bottom border-dark",
                width=1
            ),
        ],
        className="mt-2",
        no_gutters=True
    )
    return ret


def get_voc_voi_legend_fig():
    """Get Plotly figure used as voc and voi legend.

    :return: Plotly figure containing single genome legend
    :rtype: go.Figure
    """
    ret = go.Figure(get_voc_voi_legend_graph_obj())
    ret.update_layout(
        height=75,
        font={"size": 16},
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
            "pad": 0
        },
        plot_bgcolor="white",
        xaxis={
            "visible": False,
            "fixedrange": True
        },
        yaxis={
            "visible": False,
            "fixedrange": True,
            "range": [-1, 2]
        }
    )
    return ret


def get_voc_voi_legend_graph_obj():
    """Get Plotly graph obj used as voc voi legend.

    This is really just a scatterplot with a single point.

    :return: Plotly scatterplot obj containing single genome legend
    :rtype: go.Scatter
    """
    ret = go.Scatter(
        x=[0, 0],
        y=[1, 0],
        mode="text",
        text=["<i>VOI</i>", "<b>VOC</b>"],
        hoverinfo="skip"
    )
    return ret


def get_single_genome_legend_fig():
    """Get Plotly figure used as single genome legend.

    :return: Plotly figure containing single genome legend
    :rtype: go.Figure
    """
    ret = go.Figure(get_single_genome_legend_graph_obj())
    ret.update_layout(
        height=75,
        font={"size": 16},
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
            "pad": 0
        },
        plot_bgcolor="white",
        xaxis={
            "visible": False,
            "fixedrange": True
        },
        yaxis={
            "visible": False,
            "fixedrange": True,
            "range": [-1, 2]
        }
    )
    return ret


def get_single_genome_legend_graph_obj():
    """Get Plotly graph obj used as single genome legend.

    This is really just a scatterplot with a single point.

    :return: Plotly scatterplot obj containing single genome legend
    :rtype: go.Scatter
    """
    ret = go.Scatter(
        x=[0],
        y=[0],
        mode="markers+text",
        marker={
            "color": "#ffffff",
            "symbol": "square",
            "line": {"width": 2},
            "size": 30
        },
        text=["N==1"],
        textposition="top center",
        hoverinfo="skip"
    )
    return ret


def get_indel_legend_fig():
    """Get Plotly figure used as indel legend.

    :return: Plotly figure containing indel legend
    :rtype: go.Figure
    """
    ret = go.Figure(get_indel_legend_graph_obj())
    ret.update_layout(
        height=75,
        font={"size": 16},
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
            "pad": 0
        },
        plot_bgcolor="white",
        xaxis={
            "visible": False,
            "fixedrange": True,
            "range": [-1, 2]
        },
        yaxis={
            "visible": False,
            "fixedrange": True,
            "range": [-1, 2]
        }
    )
    return ret


def get_indel_legend_graph_obj():
    """Get Plotly graph obj used as indel legend.

    :return: Plotly scatterplot obj containing single genome legend
    :rtype: go.Scatter
    """
    ret = go.Scatter(
        x=[0, 1, 0, 1],
        y=[0, 0, 0, 0],
        mode="markers+text",
        marker={
            "color": ["#ffffbf", "#ffffbf", "lime", "red"],
            "symbol": ["square", "square", "cross", "x"],
            "line": {"width": 2, "color": "black"},
            "size": [30, 30, 12, 12]
        },
        text=["Ins", "Del", "", ""],
        textposition="top center",
        hoverinfo="skip"
    )
    return ret
