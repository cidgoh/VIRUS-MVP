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


def get_heatmap_row_div(data):
    """Get Dash Bootstrap Components row containing heatmap columns.

    Several columns are necessary to get the heatmap view the way we
    want it.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components row with left, center, and right
        columns producing the overall heatmap view.
    :rtype: dbc.Row
    """
    ret = dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-left-fig",
                    figure=get_heatmap_left_fig(data),
                    config={"displayModeBar": False}
                )
            ),
            width=1, style={"overflowX": "hidden"}
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-center-fig",
                    figure=get_heatmap_center_fig(data),
                    config={"displayModeBar": False},
                    # There is some sort of weirdness that
                    # overrides figure layout autosize=False value
                    # when the heatmap is re-rendered after launch,
                    # through callbacks. I suspect it is some sort
                    # of race condition between Plotly Python
                    # autosize and PlotlyJs responding to window
                    # resizing. See https://bit.ly/3nfRux2 section
                    # on responsiveness. This line fixes it,
                    # somehow.
                    style={"width": len(data["heatmap_x"]) * 25}
                ),
                style={"overflowX": "scroll"}
            ),
            width=10
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-right-fig",
                    figure=get_heatmap_right_fig(data),
                    config={"displayModeBar": False}
                ),
                style={"width": "90vw"}, className="ml-3"
            ),
            width=1, style={"overflowX": "hidden"}
        ),
    ], no_gutters=True, className="mt-3")
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
    ret = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.1, 0.9],
        vertical_spacing=0.05
    )

    # Gene bar
    heatmap_center_genes_obj = get_heatmap_center_genes_obj(data)
    ret.add_trace(heatmap_center_genes_obj, row=1, col=1)

    # This bit of hackey code is needed to display the labels on the
    # gene bar where we want them. The labels are in the middle, and
    # only appear if the bars are big enough.
    midpoints = []
    endpoints = heatmap_center_genes_obj["x"]
    for i, val in enumerate(endpoints[:-1]):
        midpoint = ((endpoints[i+1] - endpoints[i]) / 2) + endpoints[i]
        midpoints.append(midpoint)
    for i, gene_label in enumerate(heatmap_center_genes_obj["text"][0]):
        x_start = heatmap_center_genes_obj["x"][i]
        x_end = heatmap_center_genes_obj["x"][i+1]
        if (x_end - x_start) < 2:
            continue
        ret.add_annotation(
            xref="x1",
            yref="y1",
            x=midpoints[i],
            y=heatmap_center_genes_obj["y"][0],
            text=gene_label,
            showarrow=False,
            font={"color": "white"}
        )

    # Cells and x axis
    heatmap_center_base_obj = get_heatmap_center_base_obj(data)
    ret.add_trace(heatmap_center_base_obj, row=2, col=1)

    # Add lines between rows of cells
    # TODO I'm lazy--any way to not hardcode "data" here?
    our_strains = data["dir_strains"]["reference_data"]
    visible_strains = data["heatmap_y"]
    thick_line_y = \
        len([strain for strain in visible_strains if strain in our_strains])
    for y, _ in enumerate(heatmap_center_base_obj["y"]):
        if y == thick_line_y:
            width = 4
        else:
            width = 2
        ret.add_shape({
            "type": "line",
            "xref": "x2",
            "yref": "y2",
            "x0": -0.5,
            "x1": len(heatmap_center_base_obj["x"]) - 0.5,
            "y0": y-0.5,
            "y1": y-0.5,
            "line": {"width": width}
        })

    # Overlay insertions over cells
    heatmap_center_insertions_object = get_heatmap_center_insertions_obj(data)
    ret.add_trace(heatmap_center_insertions_object, row=2, col=1)

    # Overlay deletions over cells
    heatmap_center_deletions_object = get_heatmap_center_deletions_obj(data)
    ret.add_trace(heatmap_center_deletions_object, row=2, col=1)

    # Styling stuff
    ret.update_layout(xaxis1_visible=False)
    ret.update_layout(xaxis2_type="category")
    ret.update_xaxes(range=[-0.5, len(data["heatmap_x"]) - 0.5])
    ret.update_yaxes(visible=False)
    ret.update_layout(font={
        "size": 18
    })
    ret.update_layout(width=len(data["heatmap_x"]) * 25, autosize=False)
    ret.update_layout(plot_bgcolor="white")
    ret.update_layout(margin={
        "l": 0,
        "r": 0,
        "t": 0,
        "pad": 0
    })
    ret.update_xaxes(fixedrange=True)
    ret.update_yaxes(fixedrange=True)

    return ret


def get_heatmap_center_genes_obj(data):
    """Get Plotly graph object corresponding to gene bar.

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
        elif i == (len(data["heatmap_x_genes"]) - 1):
            heatmap_center_genes_obj_x.append(i+0.5)
            heatmap_center_genes_obj_labels.append(last_gene_seen)
        elif heatmap_x_gene != last_gene_seen:
            heatmap_center_genes_obj_x.append(i-0.5)
            heatmap_center_genes_obj_labels.append(last_gene_seen)
            last_gene_seen = heatmap_x_gene

    heatmap_center_genes_obj_z = [[]]
    heatmap_center_genes_obj_colorscale = []
    with open("gene_colors.json") as fp:
        gene_colors = json.load(fp)
    for i, label in enumerate(heatmap_center_genes_obj_labels):
        mock_z_val = i / (len(heatmap_center_genes_obj_labels) - 1)
        heatmap_center_genes_obj_z[0].append(mock_z_val)
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

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing cells and x axis
    :rtype: go.Heatmap
    """
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
        hoverongaps=False,
        hovertemplate="%{text}<extra></extra>",
        text=data["heatmap_cell_text"],
        xgap=10,
        ygap=10,
        showscale=False
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
    ret = go.Scatter(
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
    ret = go.Scatter(
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

    This is the y axis view. The reason we have a separate figure for
    the y axis view is that there is no native way to have a fixed y
    axis as you scroll the center heatmap figure.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap y axis
    :rtype: go.Figure
    """
    # We use subplots to line up better with the center heatmap fig.
    # The top plot is empty.
    ret = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.1, 0.9],
        vertical_spacing=0.05
    )

    # TODO: consider interactions with heatmap_left_base_obj
    heatmap_left_base_obj = get_heatmap_left_base_obj(data)
    heatmap_left_labels_obj = get_heatmap_left_labels_obj(data)

    ret.add_trace(heatmap_left_base_obj, row=2, col=1)
    ret.add_trace(heatmap_left_labels_obj, row=2, col=1)

    ret.update_layout(font={"size": 18})
    ret.update_layout(margin={
        "l": 0,
        "r": 0,
        "t": 0
    })
    ret.update_layout(plot_bgcolor="white")
    ret.update_xaxes(visible=False)
    ret.update_yaxes(visible=False)
    ret.update_xaxes(fixedrange=True)
    ret.update_yaxes(fixedrange=True)

    return ret


def get_heatmap_left_base_obj(data):
    """Get Plotly graph object of invisible, single column heatmap.

    All this object does it take up space. We overlay text over the
    cells in ``get_heatmap_left_fig`` though, to give the illusion of a
    fixed y axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing a single column,
        invisible heatmap.
    :rtype: go.Heatmap
    """
    ret = go.Heatmap(
        x=[0],
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

    This is the colorbar view. The reason we have a separate figure for
    the colorbar is that there is no native way to have a fixed
    colorbar as you scroll the center heatmap figure. This gives the
    illusion of one.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap colorbar
    :rtype: go.Figure
    """
    # We use subplots to line up better with the center heatmap fig.
    # The top plot is empty.
    ret = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.1, 0.9],
        vertical_spacing=0.05
    )

    heatmap_right_base_obj = get_heatmap_right_base_obj(data)

    ret.add_trace(heatmap_right_base_obj, row=2, col=1)
    ret.update_layout(font={"size": 18})
    ret.update_layout(plot_bgcolor="white")
    ret.update_xaxes(visible=False)
    ret.update_yaxes(visible=False)
    ret.update_layout(margin={
        "l": 0,
        "r": 0,
        "t": 0
    })
    ret.update_xaxes(fixedrange=True)
    ret.update_yaxes(fixedrange=True)

    return ret


def get_heatmap_right_base_obj(data):
    """Get Plotly graph object of colorbar.

    This is a single column heatmap with a colorbar. We have to use CSS
    styling in ``div_generator.get_heatmap_row_div`` to only show the
    colorbar. Essentially, the colorbar is on the left, and we hide the
    heatmap column on the right.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly heatmap object containing a single column and
        colorbar.
    :rtype: go.Heatmap
    """
    ret = go.Heatmap(
        x=["foo"],
        y=data["heatmap_y"],
        z=[[0] for _ in data["heatmap_y"]],
        colorscale=get_color_scale(),
        colorbar={
            "x": -2,
            "y": 0.4
        },
        zmin=0,
        zmax=1,
        hoverinfo="none"
    )
    return ret
