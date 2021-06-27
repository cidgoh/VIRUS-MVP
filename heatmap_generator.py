"""Functions for generating heatmap view.

The heatmap view is composed of several figures, because native figure
functionality did not provide the view we wanted.
"""

import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# TODO go over function docstrings


def get_color_scale():
    """Get custom Plotly color scale.

    This can be plugged into the colorscale value for Plotly heatmap
    objects.

    :return: Acceptable Plotly colorscale value, with custom colours.
    :rtype: list[list]
    """
    ret = [
        [0, "#fc8d59"],
        [1/2, "#ffffbf"],
        [1, "#91bfdb"]
    ]
    return ret


def get_heatmap_row_divs(data):
    """Get Dash Bootstrap Components row containing heatmap columns.

    Several columns are necessary to get the heatmap view the way we
    want it.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components row with left, center, and right
        columns producing the overall heatmap view.
    :rtype: dbc.Row
    """
    ret = [
        dbc.Row([
            dbc.Col([
                dbc.Row(
                    dbc.Col(
                        None,
                        style={"height": 40}
                    ), no_gutters=True
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.Graph(
                            id="heatmap-left-fig",
                            figure=get_heatmap_left_fig(data),
                            config={"displayModeBar": False}
                        )
                    ), no_gutters=True
                )],
                width=1, style={"overflowX": "hidden"}
            ),
            dbc.Col([
                dbc.Row(
                    dbc.Col(
                        dcc.Graph(
                            id="heatmap-gene-bar-fig",
                            figure=get_heatmap_gene_bar_fig(data),
                            config={"displayModeBar": False}
                        )
                    ), no_gutters=True
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.Graph(
                            id="heatmap-center-fig",
                            figure=get_heatmap_center_fig(data),
                            config={"displayModeBar": False},
                        )
                    ), no_gutters=True
                )],
                id="heatmap-center-div",
                width=10,
                style={"overflowX": "scroll"}
            ),
            dbc.Col([
                dbc.Row(
                    dbc.Col(
                        None,
                        style={"height": 40},
                    ), no_gutters=True
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.Graph(
                            id="heatmap-right-fig",
                            figure=get_heatmap_right_fig(data),
                            config={"displayModeBar": False}
                        ), className="ml-3"
                    ), no_gutters=True
                )],
                width=1, style={"overflowX": "hidden"}
            ),
        ], no_gutters=True, className="mt-3")
    ]
    return ret


def get_heatmap_gene_bar_fig(data):
    """TODO"""
    heatmap_gene_bar_obj = get_heatmap_gene_bar_obj(data)
    ret = go.Figure(heatmap_gene_bar_obj)
    ret.update_xaxes(type="linear",
                     visible=False)
    ret.update_yaxes(type="linear",
                     visible=False)
    ret.update_layout(
        width=len(data["heatmap_x"]) * 25,
        height=40,
        autosize=False,
        plot_bgcolor="white",
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
            "pad": 0
        }
    )
    # This bit of hackey code is needed to display the labels on the
    # gene bar where we want them. The labels are in the middle, and
    # appear differently if the bars are too small.
    midpoints = []
    endpoints = heatmap_gene_bar_obj["x"]
    for i, val in enumerate(endpoints[:-1]):
        midpoint = ((endpoints[i+1] - endpoints[i]) / 2) + endpoints[i]
        midpoints.append(midpoint)
    for i, gene_label in enumerate(heatmap_gene_bar_obj["text"][0]):
        x_start = heatmap_gene_bar_obj["x"][i]
        x_end = heatmap_gene_bar_obj["x"][i+1]
        # TODO: fix this hackey solution by using a monospace font, and
        #  calculating the length of the label versus the length of the
        #  gene bar cell.
        if (x_end - x_start) < 3 and len(gene_label) > (x_end - x_start):
            font_size = 10
            text_angle = 90
        else:
            font_size = 18
            text_angle = 0
        ret.add_annotation(
            xref="x1",
            yref="y1",
            x=midpoints[i],
            y=heatmap_gene_bar_obj["y"][0],
            text=gene_label,
            textangle=text_angle,
            showarrow=False,
            font={"color": "white", "size": font_size}
        )
    return ret


def get_heatmap_center_fig(data):
    """Get Plotly figure shown in the center of the heatmap div.

    This is the majority of the heatmap view. It has the cells, x axis,
    insertion markers, deletion markers, and gene bar above the
    heatmap. This figure is composed of two Plotly graph objects. An
    object on top corresponding to the gene bar, and an object on the
    bottom corresponding to the heatmap cells and x axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap cells, x axis, insertion
        markers, deletion markers, and gene bar.
    :rtype: go.Figure
    """
    # Cells and x axis
    heatmap_center_base_obj = get_heatmap_center_base_obj(data)
    heatmap_center_insertions_object = get_heatmap_center_insertions_obj(data)
    heatmap_center_deletions_object = get_heatmap_center_deletions_obj(data)
    ret = go.Figure()
    ret.add_trace(heatmap_center_base_obj)
    ret.add_trace(heatmap_center_insertions_object)
    ret.add_trace(heatmap_center_deletions_object)

    # # Styling stuff
    ret.update_layout(xaxis_type="linear")
    ret.update_layout(yaxis_type="linear")
    ret.update_xaxes(range=[-0.5, len(data["heatmap_x"])-0.5],
                     tickmode="array",
                     tickvals=list(range(len(data["heatmap_x"]))),
                     ticktext=data["heatmap_x"],
                     fixedrange=True,
                     zeroline=False,
                     showgrid=False,
                     showspikes=True,
                     spikecolor="black")
    ret.update_yaxes(range=[-0.5, len(data["heatmap_y"])-0.5],
                     tickmode="linear",
                     tick0=0.5,
                     dtick=1,
                     fixedrange=True,
                     visible=True,
                     showticklabels=False,
                     zeroline=False,
                     gridcolor="black",
                     showspikes=True,
                     spikecolor="black")
    ret.update_layout(font={
        "size": 18
    })
    ret.update_layout(
        width=len(data["heatmap_x"]) * 25,
        height=len(data["heatmap_y"]) * 30,
        autosize=False)
    ret.update_layout(plot_bgcolor="white")
    ret.update_layout(margin={
        "l": 0,
        "r": 0,
        "t": 0,
        "b": 0,
        "pad": 0
    })

    return ret


def get_heatmap_gene_bar_obj(data):
    """Get Plotly graph object corresponding to gene bar.
    TODO

    The way we produce this gene bar is quite hackey. To ensure the bar
    lines up perfectly with the main heatmap view, the gene bar is a
    heatmap itself. We use the x axis values of the main heatmap, with
    0.5 offsets to shift the gene bar cells to the middle of the main
    heatmap cells. We use mock z values to assign colors to the gene
    bar cells.

    The gene bar labels are added later in ``get_heatmap_center_fig``.
    This is because individual section gene bars are composed of
    multiple cells, so we cannot simply add labels to the cells.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing gene bar without labels
    :rtype: go.Heatmap
    """
    heatmap_center_genes_obj_x = []
    heatmap_center_genes_obj_labels = []
    last_gene_seen = ""
    for i, heatmap_x_gene in enumerate(data["heatmap_x_genes"]):
        if i == 0:
            heatmap_center_genes_obj_x.append(i-0.5)
            last_gene_seen = heatmap_x_gene
        if i == (len(data["heatmap_x_genes"]) - 1):
            heatmap_center_genes_obj_x.append(i+0.5)
            heatmap_center_genes_obj_labels.append(last_gene_seen)
        if heatmap_x_gene != last_gene_seen:
            heatmap_center_genes_obj_x.append(i-0.5)
            heatmap_center_genes_obj_labels.append(last_gene_seen)
            last_gene_seen = heatmap_x_gene

    heatmap_center_genes_obj_z = [[]]
    heatmap_center_genes_obj_colorscale = []
    with open("gene_colors.json") as fp:
        gene_colors = json.load(fp)
    for i, label in enumerate(heatmap_center_genes_obj_labels):
        mock_z_val = (i + 1) / len(heatmap_center_genes_obj_labels)
        heatmap_center_genes_obj_z[0].append(mock_z_val)
        # We add the same color to the colorscale twice, to prevent
        # things from breaking when the gene bar has only one z val.
        heatmap_center_genes_obj_colorscale.append(gene_colors[label])
        heatmap_center_genes_obj_colorscale.append(gene_colors[label])

    ret = go.Heatmap(
        x=heatmap_center_genes_obj_x,
        y=[1],
        z=heatmap_center_genes_obj_z,
        hoverinfo="skip",
        text=[heatmap_center_genes_obj_labels],
        showscale=False,
        colorscale=heatmap_center_genes_obj_colorscale
    )

    return ret


def get_heatmap_center_base_obj(data):
    """Get Plotly graph object representing heatmap cells and x axis.
    TODO

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing cells and x axis
    :rtype: go.Heatmap
    """
    scatter_y = []
    scatter_x = []
    scatter_marker_color = []
    scatter_text = []
    for i, pos in enumerate(data["heatmap_x"]):
        for j, strain in enumerate(data["heatmap_y"]):
            freq = data["heatmap_z"][j][i]
            if freq is not None:
                scatter_x.append(i)
                scatter_y.append(j)
                scatter_marker_color.append(float(freq))
                scatter_text.append(data["heatmap_cell_text"][j][i])
    ret = go.Scattergl(
        x=scatter_x,
        y=scatter_y,
        mode="markers",
        marker={
            "color": scatter_marker_color,
            "colorscale": get_color_scale(),
            "symbol": "square",
            "size": 18
        },
        hoverlabel={
            "font_size": 18
        },
        hovertemplate="%{text}<extra></extra>",
        text=scatter_text,
        showlegend=False
    )
    return ret


def get_heatmap_center_insertions_obj(data):
    """Get Plotly graph object of heatmap insertion markers.

    This is actually a scatterplot object that we overlay on the
    heatmap in ``get_heatmap_center_fig``.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly scatterplot object containing insertion markers
    :rtype: go.Scatter
    """
    ret = go.Scattergl(
        x=data["insertions_x"],
        y=data["insertions_y"],
        hoverinfo="skip",
        mode="markers",
        marker={
            "color": "lime",
            "size": 18,
            "symbol": "cross",
            "line": {"width": 2}
        },
        showlegend=False
    )
    return ret


def get_heatmap_center_deletions_obj(data):
    """Get Plotly graph object of heatmap deletion markers.

    This is actually a scatterplot object that we overlay on the
    heatmap in ``get_heatmap_center_fig``.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly scatterplot object containing deletion markers
    :rtype: go.Scatter
    """
    ret = go.Scattergl(
        x=data["deletions_x"],
        y=data["deletions_y"],
        hoverinfo="skip",
        mode="markers",
        marker={
            "color": "red",
            "size": 18,
            "symbol": "x",
            "line": {"width": 2}
        },
        showlegend=False
    )
    return ret


def get_heatmap_left_fig(data):
    """Get Plotly figure shown in the left of the heatmap div.
    TODO

    This is the y axis view. The reason we have a separate figure for
    the y axis view is that there is no native way to have a fixed y
    axis as you scroll the center heatmap figure.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap y axis
    :rtype: go.Figure
    """
    ret = go.Figure(get_heatmap_left_base_obj(data))
    ret.update_layout(
        font={"size": 18},
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
            "pad": 0
        },
        height=len(data["heatmap_y"]) * 30,
        yaxis_type="linear",
        plot_bgcolor="white"
    )
    ret.update_xaxes(visible=True,
                     fixedrange=True,
                     tickangle=90,
                     showgrid=False,
                     color="white"
                     )
    ret.update_yaxes(range=[-0.5, len(data["heatmap_y"])-0.5],
                     tickmode="linear",
                     tick0=0.5,
                     dtick=1,
                     zeroline=False,
                     visible=False,
                     fixedrange=True)
    return ret


def get_heatmap_left_base_obj(data):
    """Get Plotly graph object of invisible, single column heatmap.
    TODO

    All this object does it take up space. We overlay text over the
    cells in ``get_heatmap_left_fig`` though, to give the illusion of a
    fixed y axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing a single column,
        invisible heatmap.
    :rtype: go.Heatmap
    """
    ret = go.Scattergl(
        x=["  "+data["heatmap_x"][-1] for _ in range(len(data["heatmap_y"]))],
        y=[i for i in range(len(data["heatmap_y"]))],
        mode="text",
        text=data["heatmap_y"],
        hoverinfo="skip",
        showlegend=False
    )
    return ret


def get_heatmap_left_labels_obj(data):
    """Get Plotly graph object of y axis text.

    This is actually a scatterplot of text markers. These markers gets
    overlayed on the return value of ``get_heatmap_left_base_obj`` in
    ``get_heatmap_left_fig`` to give the illusion of a fixed y axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing a single column,
        invisible heatmap.
    :rtype: go.Scatter
    """
    ret = go.Scatter(
        y=data["heatmap_y"],
        x=[0 for _ in data["heatmap_y"]],
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
    """Get Plotly figure shown in the right of the heatmap div.
    TODO

    This is the colorbar view. The reason we have a separate figure for
    the colorbar is that there is no native way to have a fixed
    colorbar as you scroll the center heatmap figure. This gives the
    illusion of one.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap colorbar
    :rtype: go.Figure
    """
    ret = go.Figure(get_heatmap_right_base_obj(data))
    ret.update_layout(
        font={"size": 18},
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0
        },
        height=len(data["heatmap_y"])*30,
        autosize=False
    )
    ret.update_xaxes(visible=False)
    ret.update_yaxes(visible=False)
    return ret


def get_heatmap_right_base_obj(data):
    """Get Plotly graph object of colorbar.

    This is a single column heatmap with a colorbar. We have to use CSS
    styling in ``div_generator.get_heatmap_row_divs`` to only show the
    colorbar. Essentially, the colorbar is on the left, and we hide the
    heatmap column on the right.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing a single column and
        colorbar.
    :rtype: go.Heatmap
    """
    ret = go.Scattergl(
        x=[0],
        y=[0],
        mode="markers",
        marker={
            "color": [0],
            "colorscale": get_color_scale(),
            "cmin": 0,
            "cmax": 1,
            "showscale": True,
            "colorbar": {
                "x": -2
            }
        },
    )
    return ret
