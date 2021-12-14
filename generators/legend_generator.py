"""Functions for generating legend view."""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go


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
                    style={"height": "100%"}
                ),
                width={"offset": 2, "size": 1}
            )
        ],
        no_gutters=True,
        style={"height": "5vh"}
    )
    return ret


def get_voc_voi_legend_fig():
    """Get Plotly figure used as voc and voi legend.

    :return: Plotly figure containing single genome legend
    :rtype: go.Figure
    """
    ret = go.Figure(get_voc_voi_legend_graph_obj())
    ret.update_layout(
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
