"""Functions for generating table view."""

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import plotly.graph_objects as go


def get_table_row_div(data):
    """Get Dash Bootstrap Components row containing table view.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components row containing table
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        dbc.Col(
            dcc.Graph(
                id="table",
                figure=get_table_fig(data, data["heatmap_y_strains"][0]),
                config={"displayModeBar": False}
            )
        ),
    )
    return ret


def get_table_fig(data, strain):
    """Get Plotly figure representing table view.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :param strain: Strain to show table for
    :type strain: str
    :return: Plotly figure
    :rtype: go.Figure
    """
    table_obj = get_table_obj(data, strain)
    ret = go.Figure(table_obj)
    ret.update_layout(title={
        "text": strain,
        "font": {"size": 16}
    })
    return ret


def get_table_obj(data, strain):
    """Get Plotly graph object representing table view.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :param strain: Strain to show table for
    :type strain: str
    :return: Plotly graph object
    :rtype: go.Figure
    """
    # TODO these should be determined automatically based on data
    header_vals = [
        "pos", "mutation_name", "ref", "alt", "alt_freq", "functions"
    ]
    ret = go.Table(
        header={
            "values": ["<b>%s</b>" % e for e in header_vals],
            "line_color": "black",
            "fill_color": "white",
            "height": 32,
            "font": {"size": 16}
        },
        cells={
            "values": data["tables"][strain],
            "line_color": "black",
            "fill_color": "white",
            "height": 32,
            "font": {"size": 16}
        }
    )
    return ret
