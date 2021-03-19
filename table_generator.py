"""TODO..."""

import plotly.graph_objects as go


def get_table_fig(data, strain):
    """TODO..."""
    table_obj = get_table_obj(data, strain)
    ret = go.Figure(table_obj)
    ret.update_layout(title={
        "text": strain,
        "font": {"size": 24}
    })
    return ret


def get_table_obj(data, strain):
    """TODO..."""
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
            "font": {"size": 18}
        },
        cells={
            "values": data["tables"][strain],
            "line_color": "black",
            "fill_color": "white",
            "height": 32,
            "font": {"size": 18}
        }
    )
    return ret
