"""Functions for generating heatmap view.

The heatmap view is composed of several figures, because native figure
functionality did not provide the view we wanted.

We are not using the Plotly heatmap object. It is too slow. We are
using the Plotly scatter object, and making it look like a heatmap.
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
        [0, "#ffffff"],
        [0.0001, "#91bfdb"],
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
                    # Space for voc and voi legend
                    dbc.Row(
                        dbc.Col(
                            "Variants",
                            className="text-right h5",
                            style={"padding-top": 105, "padding-right": 15}
                        ),
                        style={"height": 130},
                        no_gutters=True
                    ),
                    # Space for y-axis fig; hackeyness for scrolling
                    # https://stackoverflow.com/a/49278385/11472358
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                html.Div(
                                    dcc.Graph(
                                        id="heatmap-strains-axis-fig",
                                        figure=
                                        get_heatmap_strains_axis_fig(data),
                                        config={"displayModeBar": False},
                                        style={
                                            "height": heatmap_cells_fig_height,
                                            # Need a scrollbar to match
                                            # cells fig.
                                            "width": "101%",
                                            "marginBottom":
                                                -heatmap_cells_container_height
                                        }
                                    ),
                                    id="heatmap-strains-axis-inner-container",
                                    style={
                                        "height": "100%",
                                        "overflowY": "scroll",
                                        "marginBottom":
                                            -heatmap_cells_container_height-50,
                                        "paddingBottom":
                                            heatmap_cells_container_height+50
                                    }
                                ),
                                id="heatmap-strains-axis-outer-container",
                                style={
                                    "height": heatmap_cells_container_height,
                                    "overflow": "hidden"
                                }
                            )
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
                                style={"height": 30,
                                       "width": heatmap_cells_fig_width}
                            )
                        ),
                        no_gutters=True
                    ),
                    # Protein bar above heatmap
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-nsp-bar-fig",
                                figure=get_heatmap_nsp_bar_fig(data),
                                config={"displayModeBar": False},
                                style={"height": 30,
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
                                            "marginRight":
                                                -heatmap_cells_fig_width,
                                            "marginBottom":
                                                -heatmap_cells_container_height
                                        }
                                    ),
                                    id="heatmap-cells-inner-container",
                                    style={
                                        "height": "100%",
                                        "width": "100%",
                                        "overflow": "scroll",
                                        "marginRight":
                                            -heatmap_cells_fig_width-50,
                                        "paddingRight":
                                            heatmap_cells_fig_width+50,
                                        "marginBottom":
                                            -heatmap_cells_container_height-50,
                                        "paddingBottom":
                                            heatmap_cells_container_height+50
                                    }
                                ),
                                id="heatmap-cells-outer-container",
                                style={
                                    "height": heatmap_cells_container_height,
                                    "width": heatmap_cells_fig_width,
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
                    # Empty space above sample size axis
                    dbc.Row(
                        dbc.Col(
                            "N",
                            className="h5 font-italic",
                            style={"padding-top": 105, "padding-left": 15}
                        ),
                        style={"height": 130},
                        no_gutters=True
                    ),
                    # Space for sample size axis; some hackeyness for
                    # scrolling
                    # https://stackoverflow.com/a/49278385/11472358
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                html.Div(
                                    dcc.Graph(
                                        id="heatmap-sample-size-axis-fig",
                                        figure=
                                        get_heatmap_sample_size_axis_fig(data),
                                        config={"displayModeBar": False},
                                        style={
                                            "height": heatmap_cells_fig_height,
                                            # Need a scrollbar to match
                                            # cells fig.
                                            "width": "125%",
                                            "marginBottom":
                                                -heatmap_cells_container_height
                                        }
                                    ),
                                    id="heatmap-sample-size-axis-inner-"
                                       "container",
                                    style={
                                        "height": "100%",
                                        "overflowX": "scroll",
                                        "overflowY": "scroll",
                                        "marginRight": -50,
                                        "paddingRight": 50,
                                        "marginBottom":
                                            -heatmap_cells_container_height-50,
                                        "paddingBottom":
                                            heatmap_cells_container_height+50
                                    }
                                ),
                                id="heatmap-sample-size-axis-outer-container",
                                style={
                                    "height": heatmap_cells_container_height,
                                    "overflow": "hidden"
                                }
                            )
                        ),
                        no_gutters=True
                    )
                ],
                width=1
            ),
            dbc.Col(
                [
                    # Space for single genome legend
                    dbc.Row(
                        dbc.Col(
                            "Alt freq",
                            className="h5",
                            style={"padding-top": 75}
                        ),
                        style={"height": 100},
                        no_gutters=True
                    ),
                    # Space for colorbar fig
                    dbc.Row(
                        dbc.Col(
                            dcc.Graph(
                                id="heatmap-colorbar-fig",
                                figure=get_heatmap_colorbar_fig(),
                                config={"displayModeBar": False},
                            )
                        ),
                        no_gutters=True
                    )
                ],
                width=1,
                style={"overflowX": "hidden"}
            ),
            get_mutation_details_modal()
        ],
        no_gutters=True,
        className="mt-3"
    )
    return ret


def get_heatmap_strains_axis_fig(data):
    """Get Plotly figure used as a strains y-axis for the heatmap.

    The reason we have a separate figure for the y axis view is that
    there is no native way to have a fixed y axis as you scroll the
    heatmap cells.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap strains axis
    :rtype: go.Figure
    """
    ret = go.Figure({})
    ret.update_layout(
        xaxis_type="linear",
        yaxis_type="linear",
        plot_bgcolor="white",
        font={
            "size": 16
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

    tick_text = []
    for strain in data["heatmap_y_strains"]:
        if strain in data["voc_strains"]:
            strain_text = "<b>%s</b>" % strain
        elif strain in data["voi_strains"]:
            strain_text = "<i>%s</i>" % strain
        else:
            strain_text = strain

        if data["variants_dict"][strain]:
            strain_text += " (" + data["variants_dict"][strain] + ")"

        if strain in data["circulating_strains"]:
            strain_text += "⚠️"

        tick_text.append(strain_text)

    ret.update_yaxes(range=[-0.5, len(data["heatmap_y_strains"])-0.5],
                     fixedrange=True,
                     tickmode="array",
                     tick0=0,
                     dtick=1,
                     tickvals=list(range(len(data["heatmap_y_strains"]))),
                     ticktext=tick_text,
                     ticklabelposition="outside")
    return ret


def get_heatmap_sample_size_axis_fig(data):
    """Get Plotly figure used as a sample size y-axis for the heatmap.

    The reason we have a separate figure for the y axis view is that
    there is no native way to have a fixed y axis as you scroll the
    heatmap cells.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap sample size y axis
    :rtype: go.Figure
    """
    ret = go.Figure({})
    ret.update_layout(
        xaxis_type="linear",
        yaxis_type="linear",
        plot_bgcolor="white",
        font={
            "size": 16
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 0,
            "b": 0
        }
    )
    ret.update_xaxes(fixedrange=True, visible=False)
    ret.update_yaxes(range=[-0.5, len(data["heatmap_y_sample_sizes"])-0.5],
                     fixedrange=True,
                     tickmode="array",
                     tick0=0,
                     dtick=1,
                     tickvals=list(range(len(data["heatmap_y_sample_sizes"]))),
                     ticktext=data["heatmap_y_sample_sizes"],
                     ticklabelposition="inside")
    return ret


def get_heatmap_gene_bar_fig(data):
    """Get Plotly figure used as a gene bar above the heatmap.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap gene bar
    :rtype: go.Figure
    """
    heatmap_gene_bar_obj = get_heatmap_gene_bar_graph_obj(data)
    ret = go.Figure(
        heatmap_gene_bar_obj,
        layout={
            "font": {
                "size": 16
            },
            "plot_bgcolor": "white",
            "margin": {
                "l": 0, "r": 0, "t": 0, "b": 0, "pad": 0
            },
            "xaxis": {
                "fixedrange": True,
                "range": [0, len(data["heatmap_x_genes"])],
                "type": "linear",
                "visible": False
            },
            "yaxis": {
                "fixedrange": True,
                "type": "linear",
                "visible": False
            }
        }
    )
    return ret


def get_heatmap_gene_bar_graph_obj(data):
    """Get Plotly graph object corresponding to gene bar.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly bar object containing gene bar with labels
    :rtype: go.Bar
    """
    ret_x = []
    ret_text = []
    ret_color = []

    bar_len = 0
    last_gene_seen = ""
    for i, gene in enumerate(data["heatmap_x_genes"]):
        if i == 0:
            last_gene_seen = gene
        if gene != last_gene_seen:
            ret_x.append(bar_len)
            ret_color.append(GENE_COLORS_DICT[last_gene_seen])
            if bar_len > 2:
                ret_text.append(last_gene_seen)
            else:
                ret_text.append("")

            last_gene_seen = gene
            bar_len = 0
        bar_len += 1
        if i == (len(data["heatmap_x_genes"]) - 1):
            ret_x.append(bar_len)
            ret_text.append(gene)
            ret_color.append(GENE_COLORS_DICT[gene])

    ret = go.Bar(
        x=ret_x,
        y=[1 for _ in ret_x],
        hoverinfo="skip",
        marker={
            "color": ret_color
        },
        orientation="h",
        text=ret_text,
        textposition="inside",
        insidetextanchor="middle",
        insidetextfont={"color": "white"}
    )

    return ret


def get_heatmap_nsp_bar_fig(data):
    """Get Plotly figure used as a NSP bar above the heatmap.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly figure containing heatmap NSP bar
    :rtype: go.Figure
    """
    heatmap_nsp_bar_obj = get_heatmap_nsp_bar_graph_obj(data)
    ret = go.Figure(
        heatmap_nsp_bar_obj,
        layout={
            "font": {
                "size": 16
            },
            "plot_bgcolor": "white",
            "margin": {
                "l": 0, "r": 0, "t": 0, "b": 0, "pad": 0
            },
            "xaxis": {
                "fixedrange": True,
                "range": [0, len(data["heatmap_x_nsps"])],
                "type": "linear",
                "visible": False
            },
            "yaxis": {
                "fixedrange": True,
                "type": "linear",
                "visible": False
            }
        }
    )
    return ret


def get_heatmap_nsp_bar_graph_obj(data):
    """Get Plotly graph object corresponding to NSP bar.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly bar object containing NSP bar with labels
    :rtype: go.Bar
    """
    ret_x = []
    ret_text = []

    bar_len = 0
    last_nsp_seen = ""
    for i, nsp in enumerate(data["heatmap_x_nsps"]):
        if i == 0:
            last_nsp_seen = nsp
        if nsp != last_nsp_seen:
            ret_x.append(bar_len)
            ret_text.append(last_nsp_seen)

            last_nsp_seen = nsp
            bar_len = 0
        bar_len += 1
        if i == (len(data["heatmap_x_nsps"]) - 1):
            ret_x.append(bar_len)
            ret_text.append(nsp)

    ret_text = ["" if e == "n/a" else e for e in ret_text]
    ret_color = ["purple" if e else "white" for e in ret_text]
    ret_line_width = [1 if e else 0 for e in ret_text]

    # Hackey solution for repeating NSP label
    for i, (bar_len, nsp) in enumerate(zip(ret_x, ret_text)):
        if not ret_text:
            continue
        delimiter = "".join([" " for _ in nsp])
        label_len = bar_len // 2
        if label_len:
            label = delimiter.join([nsp for _ in range(label_len)])
        # Not enough room for NSP label to fit, but we will cram it in
        else:
            label = nsp
        ret_text[i] = label

    ret = go.Bar(
        x=ret_x,
        y=[1 for _ in ret_x],
        hoverinfo="skip",
        marker={
            "color": ret_color,
            "line_width": ret_line_width
        },
        orientation="h",
        text=ret_text,
        textposition="inside",
        # Monospace to prevent issues with our hackey repeating labels
        textfont={"family": "Courier New, monospace"},
        insidetextanchor="middle",
        insidetextfont={"color": "white"}
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
            "size": 16
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
            "size": 16
        },
        margin={
            "l": 0,
            "r": 0,
            "t": 500,
            "b": 0
        }
    )
    ret.update_xaxes(range=[-0.5, len(data["heatmap_x_nt_pos"])-0.5],
                     fixedrange=True,
                     tickmode="array",
                     tickvals=data["heatmap_x_tickvals"],
                     ticktext=list(dict.fromkeys(data["heatmap_x_nt_pos"])),
                     side="top",
                     ticklabelposition="outside")
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
            "size": 16
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
    ret.update_yaxes(range=[-0.5, len(data["heatmap_y_strains"])-0.5],
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

    This is actually a scatter object, not a heatmap object. We make
    it look like a heatmap object. This is faster.

    :param data: ``data_parser.get_data`` return value
    :type data: dict
    :return: Plotly graph object containing cells
    :rtype: go.Scatter
    """
    scatter_y = []
    scatter_x = []
    scatter_marker_color = []
    scatter_text = []
    scatter_line_width = []
    for i, pos in enumerate(data["heatmap_x_nt_pos"]):
        for j, strain in enumerate(data["heatmap_y_strains"]):
            freq = data["heatmap_z"][j][i]
            if freq is not None:
                scatter_x.append(i)
                scatter_y.append(j)
                scatter_marker_color.append(float(freq))
                scatter_text.append(data["heatmap_hover_text"][j][i])

                mutation_fns = data["heatmap_mutation_fns"][j][i]
                scatter_line_width.append(2 if mutation_fns is None else 4)
    ret = go.Scatter(
        x=scatter_x,
        y=scatter_y,
        mode="markers",
        marker={
            "color": scatter_marker_color,
            "colorscale": get_color_scale(),
            "cmin": 0,
            "cmax": 1,
            "symbol": "square",
            "line": {"width": scatter_line_width},
            "size": 30
        },
        hoverlabel={
            "bgcolor": "#000000",
            "font_size": 16
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
    :rtype: go.Scatter
    """
    ret = go.Scatter(
        x=data["insertions_x"],
        y=data["insertions_y"],
        hoverinfo="skip",
        mode="markers",
        marker={
            "color": "lime",
            "size": 12,
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
    :rtype: go.Scatter
    """
    ret = go.Scatter(
        x=data["deletions_x"],
        y=data["deletions_y"],
        hoverinfo="skip",
        mode="markers",
        marker={
            "color": "red",
            "size": 12,
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
            "range": [0, 0],
            "fixedrange": True
        },
        yaxis={
            "visible": False,
            "fixedrange": True
        }
    )
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
            "color": "#ffffff",
            "colorscale": get_color_scale(),
            "cmin": 0,
            "cmax": 1,
            "showscale": True,
            "colorbar": {
                "x": 0
            }
        },
        hoverinfo="skip"
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
