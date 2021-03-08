"""TODO..."""

import plotly.graph_objects as go


def get_color_scale():
    """TODO..."""
    ret = [
        [0, "#f7fbff"],
        [1/8, "#deebf7"],
        [2/8, "#c6dbef"],
        [3/8, "#9ecae1"],
        [4/8, "#6baed6"],
        [5/8, "#4292c6"],
        [6/8, "#2171b5"],
        [7/8, "#08519c"],
        [1, "#08306b"]
    ]
    return ret


def get_heatmap_center_fig(data):
    """TODO..."""
    heatmap_center_base_obj = get_heatmap_center_base_obj(data)
    heatmap_center_insertions_object = get_heatmap_center_insertions_obj(data)
    heatmap_center_deletions_object = get_heatmap_center_deletions_obj(data)

    ret = go.Figure(heatmap_center_base_obj)
    ret.add_trace(heatmap_center_insertions_object)
    ret.add_trace(heatmap_center_deletions_object)

    ret.update_xaxes(type="category")
    ret.update_yaxes(visible=False)
    ret.update_layout(font={
        "size": 18
    })
    ret.update_layout(width=len(data["heatmap_x"]) * 25, autosize=False)
    ret.update_layout(plot_bgcolor="white")
    ret.update_layout(margin={
        "l": 0,
        "r": 0,
        "t": 0
    })

    return ret


def get_heatmap_center_base_obj(data):
    """TODO..."""
    ret = go.Heatmap(
        x=data["heatmap_x"],
        y=data["heatmap_y"],
        z=data["heatmap_z"],
        colorscale=get_color_scale(),
        zmin=0,
        zmax=1,
        hoverlabel={
            "font_size": 18
        },
        hoverinfo="text",
        text=data["heatmap_cell_text"],
        xgap=10,
        showscale=False
    )
    return ret


def get_heatmap_center_insertions_obj(data):
    """TODO..."""
    ret = go.Scatter(
        x=data["insertions_x"],
        y=data["insertions_y"],
        hoverinfo="skip",
        mode="markers",
        marker={
            "color": "lime",
            "size": 18,
            "symbol": "cross"
        },
        showlegend=False
    )
    return ret


def get_heatmap_center_deletions_obj(data):
    """TODO..."""
    ret = go.Scatter(
        x=data["deletions_x"],
        y=data["deletions_y"],
        hoverinfo="skip",
        mode="markers",
        marker={
            "color": "red",
            "size": 18,
            "symbol": "x"
        },
        showlegend=False
    )
    return ret


def get_heatmap_left_fig(data):
    """TODO..."""
    heatmap_left_base_obj = get_heatmap_left_base_obj(data)
    heatmap_left_labels_obj = get_heatmap_left_labels_obj(data)

    ret = go.Figure(heatmap_left_base_obj)
    ret.add_trace(heatmap_left_labels_obj)

    ret.update_layout(font={"size": 18})
    ret.update_layout(margin={
        "l": 0,
        "r": 0,
        "t": 0
    })
    ret.update_layout(plot_bgcolor="white")
    ret.update_xaxes(visible=False)
    ret.update_yaxes(visible=False)

    return ret


def get_heatmap_left_base_obj(data):
    """TODO..."""
    """TODO..."""
    ret = go.Heatmap(
        x=[1],
        y=data["heatmap_y"],
        z=[[0] for _ in data["heatmap_y"]],
        showscale=False,
        hoverinfo="none",
        colorscale="Greys",
        zmin=0,
        zmax=1
    )
    return ret


def get_heatmap_left_labels_obj(data):
    """TODO..."""
    ret = go.Scatter(
        y=data["heatmap_y"],
        x=[0, 0, 0],
        hoverinfo="skip",
        mode="markers+text",
        marker={
            "color": "white",
            "size": 1
        },
        text=data["heatmap_y"],
        textposition="middle center"
    )
    return ret


def get_heatmap_right_fig(data):
    """TODO..."""
    heatmap_right_base_obj = get_heatmap_right_base_obj(data)
    ret = go.Figure(heatmap_right_base_obj)
    ret.update_layout(font={"size": 18})
    ret.update_layout(plot_bgcolor="white")
    ret.update_xaxes(visible=False)
    ret.update_yaxes(visible=False)
    ret.update_layout(margin={
        "l": 0,
        "r": 0,
        "t": 0
    })
    return ret


def get_heatmap_right_base_obj(data):
    """TODO..."""
    ret = go.Heatmap(
        x=["foo"],
        y=data["heatmap_y"],
        z=[[0] for _ in data["heatmap_y"]],
        colorscale=get_color_scale(),
        colorbar={
            "x": -2
        },
        zmin=0,
        zmax=1,
        hoverinfo="none"
    )
    return ret
