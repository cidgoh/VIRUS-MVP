"""Functions for generating heatmap view.

The heatmap view is composed of several figures, because native figure
functionality did not provide the view we wanted.

We are not using the Plotly heatmap object. It is too slow. We are
using the Plotly scattergl object, and making it look like a heatmap.
"""

import json

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go


def get_main_heatmap_fig_height(data):
    """Get the height in pixels for the main heatmap fig.

    This is the fig with the heatmap cells and x-axis.

    Good to put this in a function because several other figs have to
    be the same height.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Main heatmap fig height in pixels
    :rtype: int
    """
    # Multiply the number of strains along the y-axis by some number,
    # and add a number to account for the space used by the x-axis.
    # This enables the vertical space between heatmap cells to remain
    # relatively constant as the number of strains displayed changes.
    ret = len(data["heatmap_y"])*40 + 100
    return ret


def get_color_scale():
    """Get custom Plotly color scale.

    This can be plugged into the colorscale value for Plotly graph
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


def get_heatmap_row(data):
    """Get Dash Bootstrap Components row containing heatmap columns.

    Several nested rows and columns are necessary to get the heatmap
    view the way we want it.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Dash Bootstrap Components row with multiple nested rows
        and cols for heatmap view.
    :rtype: dbc.Row
    """
    ret = dbc.Row(
        [
            dbc.Col(
                [
                    # Empty space above y axis fig
                    dbc.Row(
                        dbc.Col(
                            None,
                            style={"height": 40}
                        ),
                        no_gutters=True
                    ),
                    # Space for y-axis fig
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-y-axis-fig",
                                figure=get_heatmap_y_axis_fig(data),
                                config={"displayModeBar": False},
                                style={"width": "110%"}
                            )
                        ),
                        no_gutters=True
                    )
                ],
                className="pr-2 pr-xl-0",
                width=2,
                style={"overflowX": "visible"}
            ),
            dbc.Col(
                [
                    # Gene bar above main heatmap fig
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-gene-bar-fig",
                                figure=get_heatmap_gene_bar_fig(data),
                                config={"displayModeBar": False}
                            )
                        ),
                        no_gutters=True
                    ),
                    # Main heatmap fig with cells and x-axis
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-main-fig",
                                figure=get_heatmap_main_fig(data),
                                config={"displayModeBar": False},
                            )
                        ),
                        no_gutters=True
                    )
                ],
                id="heatmap-center-div",
                className="px-2 px-xl-0",
                width=8,
                style={"overflowX": "scroll"}
            ),
            dbc.Col(
                [
                    # Empty space above colorbar fig
                    dbc.Row(
                        dbc.Col(
                            None,
                            style={"height": 40},
                        ),
                        no_gutters=True
                    ),
                    # Space for colorbar fig
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-colorbar-fig",
                                figure=get_heatmap_colorbar_fig(data),
                                config={"displayModeBar": False},
                            ),
                            className="ml-5"
                        ),
                        no_gutters=True
                    )
                ],
                width=2,
                style={"overflowX": "hidden"}
            ),
            get_mutation_details_modal()
        ],
        no_gutters=True,
        className="mt-3"
    )
    return ret


def get_heatmap_y_axis_fig(data):
    """Get Plotly figure used as a mock y-axis for the heatmap.

    The reason we have a separate figure for the y axis view is that
    there is no native way to have a fixed y axis as you scroll the
    main heatmap figure.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap y axis
    :rtype: go.Figure
    """
    ret = go.Figure(get_heatmap_y_axis_graph_obj(data))
    ret.update_layout(
        font={"size": 18},
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
            "pad": 0
        },
        height=get_main_heatmap_fig_height(data),
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


def get_heatmap_y_axis_graph_obj(data):
    """Get Plotly graph object that forms the base of the mock y-axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly scattergl object containing text of all the strains
        as points to resemble a y-axis for the heatmap view.
    :rtype: go.Scattergl
    """
    ret = go.Scattergl(
        x=["  "+data["heatmap_x"][-1] for _ in range(len(data["heatmap_y"]))],
        y=[i for i in range(len(data["heatmap_y"]))],
        mode="text",
        text=data["heatmap_y"],
        textposition="middle left",
        hoverinfo="skip",
        showlegend=False
    )
    return ret


def get_heatmap_gene_bar_fig(data):
    """Get Plotly figure used as a gene bar above the heatmap.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap y axis
    :rtype: go.Figure
    """
    heatmap_gene_bar_obj = get_heatmap_gene_bar_graph_obj(data)
    ret = go.Figure(heatmap_gene_bar_obj)
    ret.update_xaxes(type="linear",
                     visible=False)
    ret.update_yaxes(type="linear",
                     visible=False)
    ret.update_layout(
        width=len(data["heatmap_x"]) * 36,
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


def get_heatmap_gene_bar_graph_obj(data):
    """Get Plotly graph object corresponding to gene bar.

    # TODO this is way out of date, back when we used heatmap objects
    #  instead of scatter traces. The way we implement this gene bar is
    #  too convoluted, we need to revisit this. This docstring is
    #  incorrect.

    The way we produce this gene bar is quite hackey. To ensure the bar
    lines up perfectly with the main heatmap view, the gene bar is a
    heatmap itself. We use the x axis values of the main heatmap, with
    0.5 offsets to shift the gene bar cells to the middle of the main
    heatmap cells. We use mock z values to assign colors to the gene
    bar cells.

    The gene bar labels are added later in ``get_heatmap_main_fig``.
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


def get_heatmap_main_fig(data):
    """Get Plotly figure shown that shows the heatmap cells and x-axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap cells, x-axis, insertion
        markers, and deletion markers.
    :rtype: go.Figure
    """
    ret = go.Figure(get_heatmap_main_graph_obj(data))
    ret.add_trace(get_heatmap_main_insertions_graph_obj(data))
    ret.add_trace(get_heatmap_main_deletions_graph_obj(data))

    ret.update_layout(
        xaxis_type="linear",
        yaxis_type="linear",
        width=len(data["heatmap_x"]) * 36,
        height=get_main_heatmap_fig_height(data),
        autosize=False,
        plot_bgcolor="white",
        font={
            "size": 18
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0,
            "pad": 0
        }
    )
    ret.update_xaxes(range=[-0.5, len(data["heatmap_x"])-0.5],
                     tickmode="array",
                     tickvals=list(range(len(data["heatmap_x"]))),
                     ticktext=data["heatmap_x"],
                     fixedrange=True,
                     zeroline=False,
                     gridcolor="lightgrey",
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

    return ret


def get_heatmap_main_graph_obj(data):
    """Get Plotly graph object representing heatmap cells and x axis.

    This is actually a scattergl object, not a heatmap object. We make
    it look like a heatmap object. This is faster.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly graph object containing cells and x axis
    :rtype: go.Scattergl
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
                scatter_text.append(data["heatmap_hover_text"][j][i])
    ret = go.Scattergl(
        x=scatter_x,
        y=scatter_y,
        mode="markers",
        marker={
            "color": scatter_marker_color,
            "colorscale": get_color_scale(),
            "cmin": 0,
            "cmax": 1,
            "symbol": "square",
            "line": {"width": 2},
            "size": 30
        },
        hoverlabel={
            "font_size": 18
        },
        hovertemplate="%{text}<extra></extra>",
        text=scatter_text,
        showlegend=False
    )
    return ret


def get_heatmap_main_insertions_graph_obj(data):
    """Get Plotly graph object of heatmap insertion markers.

    We overlay this on the base trace containing the cells.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly scatterplot object containing insertion markers
    :rtype: go.Scattergl
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


def get_heatmap_main_deletions_graph_obj(data):
    """Get Plotly graph object of heatmap deletion markers.

    We overlay this on the base trace containing the cells.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly scatterplot object containing deletion markers
    :rtype: go.Scattergl
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


def get_heatmap_colorbar_fig(data):
    """Get Plotly figure used as mock colorbar.

    This is the colorbar view. The reason we have a separate figure for
    the colorbar is that there is no native way to have a fixed
    colorbar as you scroll the center heatmap figure. This gives the
    illusion of one.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap colorbar
    :rtype: go.Figure
    """
    ret = go.Figure(get_heatmap_colorbar_graph_obj())
    ret.update_layout(
        font={"size": 18},
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0
        },
        autosize=False
    )
    ret.update_xaxes(visible=False)
    ret.update_yaxes(visible=False)
    return ret


def get_heatmap_colorbar_graph_obj():
    """Get Plotly graph object of colorbar.

    This is an essentially empty scatterplot with a colorbar. We're
    only interested in displaying the colorbar.

    :return: Plotly scatterplot object containing a single column and
        colorbar.
    :rtype: go.Scattergl
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
        }
    )
    return ret


def get_mutation_details_modal():
    """Returns mutation details modal.

    This modal is initially closed, and the header and body are empty.

    :return: Initially closed Dash Bootstrap Components modal for
        displaying details on mutations.
    :rtype: dbc.Modal
    """
    return dbc.Modal([
        # Empty at launch; populated when user opens modal
        dbc.ModalHeader(None, id="mutation-details-modal-header"),
        # Empty at launch; populated when user opens modal
        dbc.ModalBody(None, id="mutation-details-modal-body"),
        dbc.ModalFooter(
            dbc.Button("Close",
                       color="secondary",
                       id="mutation-details-close-btn")
        )
    ], id="mutation-details-modal", scrollable=True, size="xl")


def get_mutation_details_modal_body(mutation_fns):
    """Returns mutation details modal body.

    :param mutation_fns: A dictionary containing information on some
        mutation functions, as seen as a property for the return value
        of ``get_data``.
    :type mutation_fns: dict
    :return: A list group with displaying the information in
        ``mutation_fns``.
    :rtype: dbc.ListGroup
    """
    outer_list_group = []
    for fn_category in mutation_fns:
        inner_list_group = [dbc.ListGroupItemHeading(fn_category)]
        for fn_desc in mutation_fns[fn_category]:
            inner_list_group.append(dbc.ListGroupItemText(fn_desc))
            fn_source = mutation_fns[fn_category][fn_desc]["source"]
            fn_citation = mutation_fns[fn_category][fn_desc]["citation"]
            a = html.A(fn_citation,
                       href=fn_source,
                       target="_blank",
                       # https://bit.ly/3qQjB7Y
                       rel="noopener noreferrer")
            inner_list_group.append(dbc.ListGroupItemText(a))
        outer_list_group.append(dbc.ListGroupItem(inner_list_group))
    ret = dbc.ListGroup(outer_list_group)
    return ret
