"""Functions for generating heatmap view.

The heatmap view is composed of several figures, because native figure
functionality did not provide the view we wanted.

We are not using the Plotly heatmap object. It is too slow. We are
using the Plotly scattergl object, and making it look like a heatmap.
"""

import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go

from definitions import GENE_COLORS_DICT


def get_color_scale():
    """Get custom Plotly color scale.

    This can be plugged into the colorscale value for Plotly graph
    objects.

    :return: Acceptable Plotly colorscale value, with custom colours.
    :rtype: list[list]
    """
    ret = [
        [0, "#91bfdb"],
        [1/2, "#ffffbf"],
        [1, "#fc8d59"],
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
    heatmap_cells_fig_height = data["heatmap_cells_fig_height"]
    heatmap_cells_container_height = data["heatmap_cells_container_height"]
    heatmap_cells_fig_width = data["heatmap_cells_fig_width"]
    ret = dbc.Row(
        [
            dbc.Col(
                [
                    # Empty space above y axis fig
                    dbc.Row(
                        dbc.Col(
                            None,
                            style={"height": 100}
                        ),
                        no_gutters=True
                    ),
                    # Space for y-axis fig; hackeyness for scrolling
                    # https://stackoverflow.com/a/49278385/11472358
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                dcc.Graph(
                                    id="heatmap-y-axis-fig",
                                    figure=get_heatmap_y_axis_fig(data),
                                    config={"displayModeBar": False},
                                    style={"height": heatmap_cells_fig_height}
                                ),
                                id="heatmap-y-axis-container",
                                style={
                                    "height": "100%",
                                    "overflowY": "scroll",
                                    "direction": "rtl",
                                    "marginLeft": "-25%",
                                    "paddingLeft": "25%",
                                }
                            ),
                            style={"height": heatmap_cells_container_height,
                                   "overflow": "hidden"}
                        ),
                        no_gutters=True
                    )
                ],
                width=2,
                style={"overflowX": "visible"}
            ),
            dbc.Col(
                [
                    # Gene bar above heatmap
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-gene-bar-fig",
                                figure=get_heatmap_gene_bar_fig(data),
                                config={"displayModeBar": False},
                                style={"height": 25,
                                       "width": heatmap_cells_fig_width}
                            )
                        ),
                        no_gutters=True
                    ),
                    # Nucleotide position axis
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-nt-pos-axis-fig",
                                figure=get_heatmap_nt_pos_axis_fig(data),
                                config={"displayModeBar": False},
                                style={"height": 75,
                                       "width": heatmap_cells_fig_width}
                            )
                        )
                    ),
                    # Heatmap cells; some hackeyness for scrolling
                    # https://stackoverflow.com/a/49278385/11472358
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                html.Div(
                                    dcc.Graph(
                                        id="heatmap-cells-fig",
                                        figure=get_heatmap_cells_fig(data),
                                        config={"displayModeBar": False},
                                        style={
                                            "height": heatmap_cells_fig_height,
                                            "width": heatmap_cells_fig_width,
                                            "marginBottom":
                                                -heatmap_cells_container_height
                                        }
                                    ),
                                    id="heatmap-cells-container",
                                    style={
                                        "height": "100%",
                                        "overflowY": "scroll",
                                        "marginBottom":
                                            -heatmap_cells_container_height-50,
                                        "paddingBottom":
                                            heatmap_cells_container_height+50
                                    }
                                ),
                                style={
                                    "height": heatmap_cells_container_height,
                                    "overflow": "hidden"
                                }
                            )
                        ),
                        no_gutters=True
                    ),
                    # Amino acid axis
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-aa-pos-axis-fig",
                                figure=get_heatmap_aa_pos_axis_fig(data),
                                config={"displayModeBar": False},
                                style={"height": 140,
                                       "width": heatmap_cells_fig_width}
                            )
                        ),
                        no_gutters=True
                    ),
                ],
                id="heatmap-center-div",
                className="pl-4",
                width=8,
                style={"overflowX": "scroll"}
            ),
            dbc.Col(
                [
                    # Empty space above colorbar fig
                    dbc.Row(
                        dbc.Col(
                            None,
                            style={"height": 100},
                        ),
                        no_gutters=True
                    ),
                    # Space for colorbar fig
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-colorbar-fig",
                                figure=get_heatmap_colorbar_fig(),
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
    heatmap cells.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap y axis
    :rtype: go.Figure
    """
    ret = go.Figure({})
    ret.update_layout(
        xaxis_type="linear",
        yaxis_type="linear",
        plot_bgcolor="white",
        font={
            "size": 18
        },
        margin={
            "l": 300,
            "r": 0,
            "t": 0,
            "b": 0
        }
    )
    ret.update_xaxes(fixedrange=True,
                     visible=False)
    ret.update_yaxes(range=[-0.5, len(data["heatmap_y"])-0.5],
                     fixedrange=True,
                     tickmode="array",
                     tick0=0,
                     dtick=1,
                     tickvals=list(range(len(data["heatmap_y"]))),
                     ticktext=data["heatmap_y"],
                     ticklabelposition="outside")
    return ret


def get_heatmap_gene_bar_fig(data):
    """Get Plotly figure used as a gene bar above the heatmap.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap gene bar
    :rtype: go.Figure
    """
    heatmap_gene_bar_obj = get_heatmap_gene_bar_graph_obj(data)
    ret = go.Figure(heatmap_gene_bar_obj)
    ret.update_xaxes(type="linear",
                     fixedrange=True,
                     visible=False)
    ret.update_yaxes(type="linear",
                     fixedrange=True,
                     visible=False)
    ret.update_layout(
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
    # gene bar where we want them. The labels are in the middle.
    midpoints = []
    endpoints = heatmap_gene_bar_obj["x"]
    for i, val in enumerate(endpoints[:-1]):
        midpoint = ((endpoints[i+1] - endpoints[i]) / 2) + endpoints[i]
        midpoints.append(midpoint)
    for i, gene_label in enumerate(heatmap_gene_bar_obj["text"][0]):
        x_start = heatmap_gene_bar_obj["x"][i]
        x_end = heatmap_gene_bar_obj["x"][i + 1]
        # Too small for label
        if (x_end - x_start) < 3:
            continue
        ret.add_annotation(
            xref="x1",
            yref="y1",
            x=midpoints[i],
            y=heatmap_gene_bar_obj["y"][0],
            text=gene_label,
            showarrow=False,
            font={"color": "white", "size": 18}
        )
    return ret


def get_heatmap_gene_bar_graph_obj(data):
    """Get Plotly graph object corresponding to gene bar.

    # TODO this is way out of date, back when we used heatmap objects
    #  instead of scatter traces. The way we implement this gene bar is
    #  too convoluted, we need to revisit this. This docstring is
    #  incorrect.

    The way we produce this gene bar is quite hackey. To ensure the bar
    lines up perfectly with the heatmap cells view, the gene bar is a
    heatmap itself. We use the x axis values of the heatmap cells, with
    0.5 offsets to shift the gene bar cells to the middle of the main
    heatmap cells. We use mock z values to assign colors to the gene
    bar cells.

    The gene bar labels are added later in ``get_heatmap_cells_fig``.
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
    for i, label in enumerate(heatmap_center_genes_obj_labels):
        mock_z_val = (i + 1) / len(heatmap_center_genes_obj_labels)
        heatmap_center_genes_obj_z[0].append(mock_z_val)
        # We add the same color to the colorscale twice, to prevent
        # things from breaking when the gene bar has only one z val.
        heatmap_center_genes_obj_colorscale.append(GENE_COLORS_DICT[label])
        heatmap_center_genes_obj_colorscale.append(GENE_COLORS_DICT[label])

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


def get_heatmap_aa_pos_axis_fig(data):
    """Get Plotly figure used as amino acid position axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing amino acid axis
    :rtype: go.Figure
    """
    ret = go.Figure({})
    ret.update_layout(
        xaxis_type="linear",
        yaxis_type="linear",
        plot_bgcolor="white",
        font={
            "size": 18
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 500
        }
    )

    # Unlike nt pos axis, vals in aa pos axis can repeat. So to account
    # for heterozygous mutations we zip with nt pos values, and then
    # remove duplicates.
    zipped_axes = zip(data["heatmap_x_nt_pos"], data["heatmap_x_aa_pos"])
    tick_text = [aa for (_, aa) in dict.fromkeys(zipped_axes)]

    ret.update_xaxes(range=[-0.5, len(data["heatmap_x_nt_pos"])-0.5],
                     fixedrange=True,
                     tickmode="array",
                     tickvals=data["heatmap_x_tickvals"],
                     ticktext=tick_text,
                     ticklabelposition="outside",
                     )
    ret.update_yaxes(fixedrange=True,
                     visible=False,
                     zeroline=True)
    return ret


def get_heatmap_nt_pos_axis_fig(data):
    """Get Plotly figure used as nt pos axis.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing nt pos axis
    :rtype: go.Figure
    """
    ret = go.Figure({})
    ret.update_layout(
        xaxis_type="linear",
        yaxis_type="linear",
        plot_bgcolor="white",
        font={
            "size": 18
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0
        }
    )
    ret.update_xaxes(range=[-0.5, len(data["heatmap_x_nt_pos"])-0.5],
                     fixedrange=True,
                     tickmode="array",
                     tickvals=data["heatmap_x_tickvals"],
                     ticktext=list(dict.fromkeys(data["heatmap_x_nt_pos"])),
                     ticklabelposition="inside")
    ret.update_yaxes(fixedrange=True,
                     visible=False,
                     zeroline=True)
    return ret


def get_heatmap_cells_fig(data):
    """Get Plotly figure shown that shows the heatmap cells.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap cells, insertion
        markers, and deletion markers.
    :rtype: go.Figure
    """
    ret = go.Figure(get_heatmap_cells_graph_obj(data))
    ret.add_trace(get_heatmap_main_insertions_graph_obj(data))
    ret.add_trace(get_heatmap_main_deletions_graph_obj(data))

    ret.update_layout(
        xaxis_type="linear",
        yaxis_type="linear",
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
    ret.update_xaxes(range=[-0.5, len(data["heatmap_x_nt_pos"])-0.5],
                     tickmode="array",
                     tickvals=data["heatmap_cells_tickvals"],
                     fixedrange=True,
                     visible=True,
                     showticklabels=False,
                     zeroline=False,
                     gridcolor="grey",
                     showspikes=True,
                     spikecolor="black",
                     side="top")
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


def get_heatmap_cells_graph_obj(data):
    """Get Plotly graph object representing heatmap cells.

    This is actually a scattergl object, not a heatmap object. We make
    it look like a heatmap object. This is faster.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly graph object containing cells
    :rtype: go.Scattergl
    """
    scatter_y = []
    scatter_x = []
    scatter_marker_color = []
    scatter_text = []
    for i, pos in enumerate(data["heatmap_x_nt_pos"]):
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


def get_heatmap_colorbar_fig():
    """Get Plotly figure used as mock colorbar.

    This is the colorbar view. The reason we have a separate figure for
    the colorbar is that there is no native way to have a fixed
    colorbar as you scroll the center heatmap figure. This gives the
    illusion of one.

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
