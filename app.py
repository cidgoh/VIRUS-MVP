"""Entry point of the application.

This is the Python script that is run to launch the visualization
application.

Dash expects you to place all your Python callbacks in this file, so
that is what I have done. This file is quite long and unmodularized as
a result. There are some callbacks that are written in JavaScript,
which are referenced in this file, but implemented in
``assets/script.js``.

Dash will execute callbacks in parallel when given the opportunity,
and I have setup my callbacks to take advantage of this for performance
benefits. However, due to what I assume is a limited number of workers,
I have unparallelized some callbacks, which allows certain callbacks to
run faster.
"""

from time import sleep

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import ALL, ClientsideFunction, Input, Output, State
from dash.exceptions import PreventUpdate

from data_parser import get_data
from definitions import ASSETS_DIR, REFERENCE_DATA_DIR
from generators import (heatmap_generator, histogram_generator,
                        table_generator, toolbar_generator, footer_generator)


# This is the only global variable Dash plays nice with, and it
# contains the visualization that is deployed by this file, when
# ``app`` is served.
app = dash.Dash(
    name="COVID-MVP",
    assets_folder=ASSETS_DIR,
    # We bring in jQuery for some of the JavaScript
    # callbacks.
    external_scripts=[
        "https://code.jquery.com/jquery-2.2.4.min.js",
        "https://code.jquery.com/ui/1.12.1/jquery-ui.min.js",
    ],
    # We can use bootstrap CSS.
    # https://bit.ly/3tMqY0W for details.
    external_stylesheets=[dbc.themes.COSMO],
    # Callbacks break without this, because they reference
    # divs that are not present on initial page load, or
    # until ``launch_app`` has finished executing.
    suppress_callback_exceptions=True
)
# server instance used for gunicorn deployment
server = app.server

# The ``layout`` attribute determines what HTML ``app`` renders when it
# is served. We start with an empty bootstrap container, but it will be
# populated soon after by the ``launch_app`` callback.
app.layout = dbc.Container(
    # ``first-launch`` is an in-browser variable, which is only used
    # when the page is first loaded. Assigning this variable here
    # triggers the ``launch_app`` callback, which populates this
    # container with the appropriate content when the page is first
    # loaded. More detail on why this is necessary is in the callback
    # docstring.
    dcc.Store("first-launch"),
    fluid=True,
    id="main-container",
    className="px-0"
)


@app.callback(
    Output("main-container", "children"),
    Input("first-launch", "data")
)
def launch_app(_):
    """Populate empty container in initial layout served by ``app``.
    *also

    This not only adds HTML, but also several in-browser variables that
    are useful for triggering other callbacks.

    When the ``first-launch`` in-browser variable is assigned, it
    triggers this callback. This callback should not be triggered
    again. This callback is only used to serve HTML and in-browser
    variables once, when the application is first launched and the main
    container is created.

    Generating the content below with a callback, instead of in the
    global scope, prevents the application from breaking on page
    reload. Dash is stateless, so it does not recalculate global
    variables on page refreshes after the application is first deployed
    to a server. So new data between page reloads may not be displayed
    if you do the following in the global scope--which you may be
    tempted to do because we are only doing it once!
    """
    data_ = get_data([REFERENCE_DATA_DIR])
    return [
        # Bootstrap row containing tools at the top of the application
        toolbar_generator.get_toolbar_row(data_),
        # Bootstrap row containing heatmap
        heatmap_generator.get_heatmap_row(data_),
        # Bootstrap row containing histogram
        histogram_generator.get_histogram_row(data_),
        # Bootstrap row containing table
        table_generator.get_table_row_div(data_),
        # Bootstrap row containing footer
        footer_generator.get_footer_row_div(
            app.get_asset_url("cidgoh_logo.png")
        ),
        # These are in-browser variables that Dash can treat as Inputs and
        # Outputs, in addition to more conventional Dash components like
        # HTML divs and Plotly figures. ``data`` is the data used to
        # generate the heatmap and table. A bit confusing, but dcc.Store
        # variables have data attributes. So ``data`` has a ``data``
        # attribute.
        dcc.Store(id="data", data=data_),
        # The following in-browser variables simply exist to help
        # modularize the callbacks below.
        dcc.Store(id="show-clade-defining"),
        dcc.Store(id="hidden-strains"),
        dcc.Store(id="strain-order"),
        dcc.Store(id="last-heatmap-cell-clicked"),
        # Used to update certain figures only when necessary
        dcc.Store(id="heatmap-x-len", data=len(data_["heatmap_x_nt_pos"])),
        dcc.Store(id="heatmap-y", data=len(data_["heatmap_y"])),
        # Used to integrate some JS callbacks. The data values are
        # meaningless, we just need outputs to perform all clientside
        # functions.
        dcc.Store(id="make-select-lineages-modal-checkboxes-draggable"),
        dcc.Store(id="make-histogram-rel-pos-bar-dynamic"),
        dcc.Store(id="link-heatmap-cells-y-scrolling")
    ]


@app.callback(
    Output("data", "data"),
    inputs=[
        Input("show-clade-defining", "data"),
        Input("hidden-strains", "data"),
        Input("strain-order", "data"),
        Input("mutation-freq-slider", "value")
    ],
    prevent_initial_call=True
)
def update_data(show_clade_defining, hidden_strains, strain_order,
                mutation_freq_vals):
    """Update ``data`` variable in dcc.Store.

    This is a central callback. It triggers a change to the ``data``
    variable in dcc.Store, which triggers cascading changes in several
    divs. This function receives multiple inputs, corresponding to
    different ways the ``data`` variable could be changed.

    :param show_clade_defining: ``update_show_clade-defining`` return
        value.
    :type show_clade_defining: bool
    :param hidden_strains: ``update_hidden_strains`` return value
    :type hidden_strains: list[str]
    :param strain_order: ``getStrainOrder`` return value from
        ``script.js``.
    :type strain_order: list[str]
    :param mutation_freq_vals: Position of handles in mutation freq
        slider.
    :type mutation_freq_vals: list[int|float]
    :param gff3_annotations: ``parse_gff3_file`` return value
    :type gff3_annotations: dict
    :return: ``get_data`` return value
    :rtype: dict
    :raise PreventUpdate: New upload triggered this function, and that
        new upload failed.
    """
    triggers = [x["prop_id"] for x in dash.callback_context.triggered]

    # Do not use the current position of the mutation frequency slider
    # if this function was triggered by an input that will modify the
    # slider values. We must reset the slider in that case to avoid
    # bugs.
    use_mutation_freq_vals = "mutation-freq-slider.value" in triggers
    use_mutation_freq_vals |= "strain-order.data" in triggers
    if use_mutation_freq_vals:
        [min_mutation_freq, max_mutation_freq] = mutation_freq_vals
    else:
        min_mutation_freq, max_mutation_freq = None, None

    return get_data([REFERENCE_DATA_DIR],
                    clade_defining=show_clade_defining,
                    hidden_strains=hidden_strains,
                    strain_order=strain_order,
                    min_mutation_freq=min_mutation_freq,
                    max_mutation_freq=max_mutation_freq)


@app.callback(
    Output("show-clade-defining", "data"),
    Input("clade-defining-mutations-switch", "value"),
    prevent_initial_call=True
)
def update_show_clade_defining(switches_value):
    """Update ``show_clade_defining`` variable in dcc.Store.

    This should be set to True when the clade defining mutations switch
    is switched on, and False when it is turned off. It is None at
    application launch.

    :param switches_value: ``[1]`` if the clade defining mutation
        switch is switched on, and ``[]`` if it is not.
    :type switches_value: list
    :return: True if clade defining mutations switch is switched on
    :rtype: bool
    """
    return len(switches_value) > 0


@app.callback(
    Output("dialog-col", "children"),
    Input("mutation-freq-slider", "marks"),
    prevent_initial_call=True
)
def update_dialog_col(_):
    """Update ``dialog-col`` div in toolbar.

    This function shows an error alert when there was an unsuccessful
    upload by the user, or the mutation frequency slider was
    re-rendered. In a hackey way, this function triggers
    ``hide_dialog_col``, which hides the dialog col after some time.

    :param _: Unused input variable that allows re-rendering of the
        mutation frequency slider to trigger this function.
    :return: Dash Bootstrap Components alert if new_upload describes an
        unsuccessfully uploaded file.
    :rtype: dbc.Alert
    """
    triggers = [x["prop_id"] for x in dash.callback_context.triggered]

    if "mutation-freq-slider.marks" in triggers:
        return dbc.Fade(
            dbc.Alert("Mutation frequency slider values reset.",
                      color="warning",
                      className="mb-0 p-1 d-inline-block"),
            id="temp-dialog-col",
            style={"transition": "all 500ms linear 0s"}
        )


@app.callback(
    Output("temp-dialog-col", "is_in"),
    Input("temp-dialog-col", "children")
)
def hide_dialog_col(_):
    """Hides newly generated ``dialog-col`` divs after five seconds.

    :param _: Unused input variable that allows generation of
        ``temp-dialog-col`` in ``update_dialog_col`` to trigger this
        function.
    :return: Property that fades newly generated ``dialog-col`` out.
    :rtype: bool
    """
    sleep(5)
    return False


@app.callback(
    Output("hidden-strains", "data"),
    Input("select-lineages-ok-btn", "n_clicks"),
    State({"type": "select-lineages-modal-checklist", "index": ALL}, "value"),
    State("data", "data"),
    prevent_initial_call=True
)
def update_hidden_strains(_, values, data):
    """Update ``hidden-strains`` variable in dcc.Store.

    When the OK button is clicked in the select lineages modal, the
    unchecked boxes are returned as the new ``hidden-strains`` value.

    :param _: Otherwise useless input only needed to alert us when the
        ok button in the select lineages modal was clicked.
    :param values: List of lists, with the nested lists containing
        strains from different directories, that had checked boxes when
        the select lineages modal was closed.
    :type values: list
    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict
    :return: List of strains that should not be displayed by the
        heatmap or table.
    :rtype: list[str]
    :raise PreventUpdate: Hidden strains did not change, or the user
        chose to hide all strains.
    """
    # Merge list of lists into single list. I got it from:
    # https://stackoverflow.com/a/716761/11472358.
    checked_strains = [j for i in values for j in i]

    all_strains = data["all_strains"]
    hidden_strains = []
    for strain in all_strains:
        if strain not in checked_strains:
            hidden_strains.append(strain)

    old_hidden_strains = data["hidden_strains"]
    no_change = hidden_strains == old_hidden_strains
    all_hidden = hidden_strains == all_strains
    if no_change or all_hidden:
        raise PreventUpdate

    return hidden_strains


@app.callback(
    Output("select-lineages-modal", "is_open"),
    Output("select-lineages-modal-body", "children"),
    Input("open-select-lineages-modal-btn", "n_clicks"),
    Input("select-lineages-ok-btn", "n_clicks"),
    Input("select-lineages-cancel-btn", "n_clicks"),
    State("data", "data"),
    prevent_initial_call=True
)
def toggle_select_lineages_modal(_, __, ___, data):
    """Open or close select lineages modal.

    Not only is this function in charge of opening or closing the
    select lineages modal, it is also in charge of dynamically
    populating the select lineages modal body when the modal is opened.

    :param _: Select lineages button in toolbar was clicked
    :param __: OK button in select lineages modal was clicked
    :param ___: Cancel button in select lineages modal was clicked
    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict
    :return: Boolean representing whether the select lineages modal is
        open or closed, and content representing the select lineages
        modal body.
    :rtype: (bool, list[dbc.FormGroup])
    """
    ctx = dash.callback_context
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    # We only open the modal when the select lineages modal btn in the
    # toolbar is clicked.
    if triggered_prop_id == "open-select-lineages-modal-btn.n_clicks":
        modal_body = toolbar_generator.get_select_lineages_modal_body(data)
        return True, modal_body
    else:
        # No need to populate modal body if the modal is closed
        return False, None


@app.callback(
    Output("mutation-freq-slider-col", "children"),
    Input("data", "data"),
    State("mutation-freq-slider", "marks"),
    prevent_initial_call=True
)
def update_mutation_freq_slider(data, old_slider_marks):
    """Update mutation frequency slider div.

    If the ``data`` dcc variable is updated, this function will
    re-render the slider if the new ``data`` variable has a different
    set of mutation frequencies.

    :param data: ``get_data`` return value, transported here by
        ``update_data``.
    :type data: dict
    :param old_slider_marks: ``marks`` property of the current
        mutation frequency slider div.
    :type old_slider_marks: dict
    :return: New mutation frequency slider div, if one is needed
    :rtype: dcc.RangeSlider
    :raise PreventUpdate: Number of mutation frequencies in ``data`` is
        different than the number of mutation frequencies in the
        current slider.
    """
    # This is very hackey, but also very fast. I do not think this will
    # currently break anything.
    new_slider_marks = data["mutation_freq_slider_vals"]
    if len(new_slider_marks) == len(old_slider_marks):
        raise PreventUpdate

    return toolbar_generator.get_mutation_freq_slider(data)


@app.callback(
    Output("heatmap-x-len", "data"),
    Input("data", "data"),
    State("heatmap-x-len", "data"),
    prevent_initial_call=True
)
def route_data_heatmap_x_update(data, old_heatmap_x_len):
    """Update ``heatmap-x-len`` dcc variable when needed.

    This serves as a useful trigger for figs that only need to be
    updated when heatmap x coords change. We use the length of
    data["heatmap_x_nt_pos"] because it is faster than comparing the
    entire list, and appropriately alerts us when
    data["heatmap_x_nt_pos"] changed.

    :param data: ``get_data`` return value, transported here by
        ``update_data``.
    :type data: dict
    :param old_heatmap_x_len: ``heatmap-x-len.data`` value
    :type old_heatmap_x_len: dict
    :return: New len of data["heatmap_x_nt_pos"]
    :rtype: int
    :raise PreventUpdate: If data["heatmap_x_nt_pos"] len did not
        change.
    """
    if old_heatmap_x_len == len(data["heatmap_x_nt_pos"]):
        raise PreventUpdate
    return len(data["heatmap_x_nt_pos"])


@app.callback(
    Output("heatmap-y", "data"),
    Input("data", "data"),
    State("heatmap-y", "data"),
    prevent_initial_call=True
)
def route_data_heatmap_y_update(data, old_heatmap_y):
    """Update ``heatmap-y`` dcc variable when needed.

    This serves as a useful trigger for figs that only need to be
    updated when heatmap y changes.

    :param data: ``get_data`` return value, transported here by
        ``update_data``.
    :type data: dict
    :param old_heatmap_y: ``heatmap-y.data`` value
    :type old_heatmap_y: dict
    :return: New len of data["heatmap_y"]
    :rtype: int
    :raise PreventUpdate: If data["heatmap_y"] len did not change
    """
    if old_heatmap_y == data["heatmap_y"]:
        raise PreventUpdate
    return data["heatmap_y"]


@app.callback(
    Output("heatmap-y-axis-fig", "figure"),
    Output("heatmap-y-axis-fig", "style"),
    Output("heatmap-y-axis-inner-container", "style"),
    Output("heatmap-y-axis-outer-container", "style"),
    Input("heatmap-y", "data"),
    State("data", "data"),
    prevent_initial_call=True
)
def update_heatmap_y_axis_fig(_, data):
    """Update heatmap y axis fig and containers.

    We need to update style because attributes may change due to
    uploaded strains.

    :param _: Heatmap cells fig updated
    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict
    :return: New heatmap y axis fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    y_axis_fig = heatmap_generator.get_heatmap_y_axis_fig(data)
    y_axis_style = {"height": data["heatmap_cells_fig_height"],
                    "width": "101%",
                    "marginBottom": -data["heatmap_cells_container_height"]}
    inner_container_style = {
        "height": "100%",
        "overflowY": "scroll",
        "marginBottom":
            -data["heatmap_cells_container_height"]-50,
        "paddingBottom":
            data["heatmap_cells_container_height"]+50
    }
    outer_container_style = {
        "height": data["heatmap_cells_container_height"],
        "overflow": "hidden"
    }
    return (y_axis_fig, y_axis_style, inner_container_style,
            outer_container_style)


@app.callback(
    Output("heatmap-gene-bar-fig", "figure"),
    Output("heatmap-gene-bar-fig", "style"),
    Input("heatmap-x-len", "data"),
    State("data", "data"),
    prevent_initial_call=True
)
def update_heatmap_gene_bar_fig(_, data):
    """Update heatmap gene bar fig.

    We need to update style because width might have changed due to
    added nt positions in data.

    :param _: Heatmap cells fig updated
    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict
    :return: New heatmap gene bar fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    gene_bar_fig = heatmap_generator.get_heatmap_gene_bar_fig(data)
    gene_bar_style = {"width": data["heatmap_cells_fig_width"]}
    return gene_bar_fig, gene_bar_style


@app.callback(
    Output("heatmap-nt-pos-axis-fig", "figure"),
    Output("heatmap-nt-pos-axis-fig", "style"),
    Input("heatmap-x-len", "data"),
    State("data", "data"),
    prevent_initial_call=True
)
def update_heatmap_nt_pos_axis_fig(_, data):
    """Update heatmap nt pos axis fig.

    We need to update style because width might have changed due to
    added nt positions in data.

    :param _: Heatmap cells fig updated
    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict
    :return: New heatmap nt pos x-axis fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    nt_pos_x_axis_fig = heatmap_generator.get_heatmap_nt_pos_axis_fig(data)
    nt_pos_x_axis_style = {"width": data["heatmap_cells_fig_width"]}
    return nt_pos_x_axis_fig, nt_pos_x_axis_style


@app.callback(
    Output("heatmap-aa-pos-axis-fig", "figure"),
    Output("heatmap-aa-pos-axis-fig", "style"),
    Input("heatmap-x-len", "data"),
    State("data", "data"),
    prevent_initial_call=True
)
def update_heatmap_aa_pos_axis_fig(_, data):
    """Update heatmap amino acid position axis fig.

    We need to update style because width might have changed due to
    added nt positions in data.

    :param _: Heatmap cells fig updated
    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict
    :return: New heatmap amino acid position x-axis fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    aa_pos_x_axis_fig = heatmap_generator.get_heatmap_aa_pos_axis_fig(data)
    aa_pos_x_axis_style = {"width": data["heatmap_cells_fig_width"]}
    return aa_pos_x_axis_fig, aa_pos_x_axis_style


@app.callback(
    Output("histogram-top-row-div", "children"),
    Input("data", "data"),
    prevent_initial_call=True
)
def update_histogram(data):
    """Update histogram top row div.

    When the ``data`` variable in the dcc.Store is updated, the top row
    in the histogram view is updated to reflect the new data. This
    includes the actual histogram bars, and the y axis.

    :param data: ``get_data`` return value, transported here by
    :type data: dict
    :return: New histogram figure corresponding to new data
    :rtype: plotly.graph_objects.Figure
    """
    return histogram_generator.get_histogram_top_row(data)

@app.callback(
    Output("heatmap-cells-fig", "figure"),
    Output("heatmap-cells-fig", "style"),
    Output("heatmap-cells-inner-container", "style"),
    Output("heatmap-cells-outer-container", "style"),
    Input("data", "data"),
    prevent_initial_call=True
)
def update_heatmap_cells_fig(data):
    """Update heatmap cells fig, style, and containers.

    This is the fig with the heatmap cells and x axis. We return style
    because attributes may need to change due to changes in data.

    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict
    :return: New heatmap cells fig
    :rtype: plotly.graph_objects.Figure
    """
    cells_fig = heatmap_generator.get_heatmap_cells_fig(data)
    cells_fig_style = {
        "height": data["heatmap_cells_fig_height"],
        "width": data["heatmap_cells_fig_width"],
        "marginRight": -data["heatmap_cells_fig_width"],
        "marginBottom": -data["heatmap_cells_container_height"]
    }
    inner_container_style = {
        "height": "100%",
        "width": "100%",
        "overflow": "scroll",
        "marginRight":
            -data["heatmap_cells_fig_width"]-50,
        "paddingRight":
            data["heatmap_cells_fig_width"]+50,
        "marginBottom":
            -data["heatmap_cells_container_height"]-50,
        "paddingBottom":
            data["heatmap_cells_container_height"]+50
    }
    outer_container_style = {
        "height": data["heatmap_cells_container_height"],
        "width": data["heatmap_cells_fig_width"],
        "overflow": "hidden"
    }
    return (cells_fig, cells_fig_style, inner_container_style,
            outer_container_style)


@app.callback(
    Output("heatmap-cells-fig", "clickData"),
    Output("last-heatmap-cell-clicked", "data"),
    Input("heatmap-cells-fig", "clickData"),
    prevent_initial_call=True
)
def route_heatmap_cells_fig_click(click_data):
    """Store click data from heatmap in "last-heatmap-cell-clicked".

    The built-in ``clickData`` variable does not allow repeated
    callbacks following consecutive clicks of the same point. We get
    around this by receiving the ``clickData``, storing it in
    ``last-heatmap-cell-clicked``, and setting ``clickData`` to None.
    When ``clickData`` is set to None, it can be updated by clicking
    the same point again, which triggers ``last-heatmap-cell-clicked``
    to be updated as well. ``last-heatmap-cell-clicked`` is the
    clickData input detected by callbacks.

    The logical question is, "why do the callbacks not just use
    ``clickData`` as input, and reset it to None each time? Why use
    this middle-man?" Because multiple callbacks use ``clickData`` in
    parallel, and if you reset it to None in one when that callback is
    finished, the other callbacks may not receive it in time. We never
    reset ``last-heatmap-cell-clicked`` to None in any callbacks,
    because we do not need to.

    :param click_data: ``heatmap-cells-fig.clickData`` value
    :type click_data: dict
    :return: ``None`` to reset heatmap ``clickData`` attribute, and a
        copy of  this attribute before resetting
    :rtype: (None, dict)
    """
    return None, click_data


@app.callback(
    Output("mutation-details-modal", "is_open"),
    Output("mutation-details-modal-header", "children"),
    Output("mutation-details-modal-body", "children"),
    Input("last-heatmap-cell-clicked", "data"),
    Input("mutation-details-close-btn", "n_clicks"),
    State("data", "data"),
    prevent_initial_call=True
)
def toggle_mutation_details_modal(click_data, _, data):
    """Open or close mutation details modal.

    Not only is this function in charge of opening or closing the
    mutation details modal, it is also in charge of dynamically
    populating the mutation details modal body when the modal is
    opened.

    :param click_data: ``last-heatmap-cell-clicked`` in-browser
        variable value.
    :type click_data: dict
    :param _: Close button in mutation details modal was clicked
    :param data: Current value for ``data`` variable; see ``get_data``
        return value.
    :type data: dict or None
    :return: Boolean representing whether the mutation details modal is
        open or closed, mutation details modal header, and mutation
        details body.
    :rtype: (bool, str, dbc.ListGroup)"""
    ctx = dash.callback_context
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    # We only open the modal when the heatmap is clicked
    if triggered_prop_id == "last-heatmap-cell-clicked.data":
        x = click_data["points"][0]["x"]
        y = click_data["points"][0]["y"]
        mutation_name = data["heatmap_mutation_names"][y][x]
        if not mutation_name:
            mutation_name = "No recorded mutation name"
        mutation_fns = data["heatmap_mutation_fns"][y][x]
        if not mutation_fns:
            body = "No functions recorded so far"
        else:
            body = \
                heatmap_generator.get_mutation_details_modal_body(mutation_fns)
        return True, mutation_name, body
    else:
        # No need to populate modal body if the modal is closed
        return False, None, None


@app.callback(
    Output("table", "figure"),
    inputs=[
        Input("data", "data"),
        Input("last-heatmap-cell-clicked", "data"),
    ],
    prevent_initial_call=True
)
def update_table(data, click_data):
    """Update table figure.

    When the ``data`` variable in the dcc.Store is updated, the table
    figure is updated as well. The table figure is also updated when
    the user clicks a heatmap cell. If no cell was clicked, a default
    strain is shown.

    :param data: ``get_data`` return value, transported here by
    :type data: dict
    :param click_data: ``last-heatmap-cell-clicked`` in-browser
        variable value.
    :type click_data: dict
    :return: New table figure corresponding to new data, or user
        selected strain.
    :rtype: plotly.graph_objects.Figure
    """
    ctx = dash.callback_context
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    if triggered_prop_id == "data.data":
        table_strain = data["heatmap_y"][0]
    else:
        table_strain = data["heatmap_y"][click_data["points"][0]["y"]]

    # If you click a strain, but then hide it, this condition stops
    # things from breaking.
    if table_strain in data["hidden_strains"]:
        table_strain = data["heatmap_y"][0]

    return table_generator.get_table_fig(data, table_strain)


# This is how Dash allows you to write callbacks in JavaScript
app.clientside_callback(
    ClientsideFunction(
        namespace="clientside",
        function_name="makeSelectLineagesModalCheckboxesDraggable"
    ),
    Output("make-select-lineages-modal-checkboxes-draggable", "data"),
    Input({"type": "select-lineages-modal-checklist", "index": ALL}, "id"),
    prevent_initial_call=True
)
app.clientside_callback(
    ClientsideFunction(
        namespace="clientside",
        function_name="getStrainOrder"
    ),
    Output("strain-order", "data"),
    Input("select-lineages-ok-btn", "n_clicks"),
    State({"type": "select-lineages-modal-checklist", "index": ALL}, "id"),
    State("data", "data"),
    prevent_initial_call=True
)
app.clientside_callback(
    ClientsideFunction(
        namespace="clientside",
        function_name="makeHistogramRelPosBarDynamic"
    ),
    Output("make-histogram-rel-pos-bar-dynamic", "data"),
    Input("heatmap-nt-pos-axis-fig", "figure"),
    State("data", "data")
)
app.clientside_callback(
    ClientsideFunction(
        namespace="clientside",
        function_name="linkHeatmapCellsYScrolling"
    ),
    Output("link-heatmap-cells-y-scrolling", "data"),
    Input("heatmap-y-axis-fig", "figure"),
    Input("heatmap-cells-fig", "figure")
)

if __name__ == "__main__":
    # Serve ``app``
    app.run_server(debug=True, host='0.0.0.0')
