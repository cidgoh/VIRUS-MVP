"""Functions for generating legend view."""

import dash_bootstrap_components as dbc


def get_legend_row():
    """TODO"""
    ret = dbc.Row(
        dbc.Col(
            "Hello world!",
            width={"offset": 2, "size": 8}
        ),
        no_gutters=True
    )
    return ret
