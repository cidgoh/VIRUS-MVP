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
from json import loads
from os import path, walk
from shutil import copytree, make_archive
from tempfile import TemporaryDirectory
from time import sleep

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import (ALL, MATCH, ClientsideFunction, Input, Output,
                               State)
from dash.exceptions import PreventUpdate
from flask_caching import Cache

from data_parser import get_data
from definitions import (ASSETS_DIR, REFERENCE_DATA_DIR,
                         REFERENCE_SURVEILLANCE_REPORTS_DIR)
from generators import (heatmap_generator, histogram_generator,
                        legend_generator, table_generator, toolbar_generator,
                        footer_generator)


# This is the only global variable Dash plays nice with, and it
# contains the visualization that is deployed by this file, when
# ``app`` is served.
app = dash.Dash(
    name="COVID-MVP",
    title="COVID-MVP",
    assets_folder=ASSETS_DIR,
    # We bring in jQuery for some of the JavaScript
    # callbacks.
    external_scripts=[
        "https://code.jquery.com/jquery-2.2.4.min.js",
        "https://code.jquery.com/ui/1.12.1/jquery-ui.min.js",
    ],
    # We can use bootstrap CSS.
    # https://bit.ly/3tMqY0W for details.
    external_stylesheets=[
        dbc.themes.COSMO,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.0/font/"
        "bootstrap-icons.css"
    ],
    # Callbacks break without this, because they reference
    # divs that are not present on initial page load, or
    # until ``launch_app`` has finished executing.
    suppress_callback_exceptions=True
)
# server instance used for gunicorn deployment
server = app.server

# Cache specifications
cache = Cache(server, config={
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": "cache_directory",
    # Max number of files app will store before it starts deleting some
    "CACHE_THRESHOLD": 200
})
# Cache lasts for a day
TIMEOUT = 86400

# The ``layout`` attribute determines what HTML ``app`` renders when it
# is served. We start with an empty bootstrap container, but it will be
# populated soon after by the ``launch_app`` callback.
app.layout = dbc.Container(
    # ``first-launch`` is an in-browser variable, which is only used
    # when the page is first loaded. Assigning this variable here
    # triggers the ``launch_app`` callback, which populates this
    # container with the appropriate content when the page is first
    # loaded. More detail on why this is necessary is in the callback
    # docstring. ``first-launch-loader`` is also only used when the
    # page is first loaded, but ultimately excised from the page.
    [
        dcc.Loading(None,
                    id="first-launch-loader",
                    style={"height": "100%", "width": "100%", "margin": 0}),
        dcc.Store("first-launch"),
    ],
    fluid=True,
    id="main-container",
    className="px-0"
)


@app.callback(
    Output("main-container", "children"),
    Output("first-launch-loader", "children"),
    Input("first-launch", "data")
)
def launch_app(_):
    """Populate empty container in initial layout served by ``app``.

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

    We also technically return the children for
    ``first-launch-loader``, but the return value is the same as its
    current value (``None``), and since ``first-launch-loader`` is in
    ``main-container``, its immediately excised from the page after
    this callback. The ultimate purpose of this is to replace the blank
    loading screen when the app is first loaded.
    """
    # Some default vals
    get_data_args = {
        "show_clade_defining": False,
        "hidden_strains": [],
        "strain_order": [],
        "min_mutation_freq": None,
        "max_mutation_freq": None
    }
    last_data_mtime = \
        max(path.getmtime(root) for root, _, _ in walk(REFERENCE_DATA_DIR))
    data_ = read_data(get_data_args, last_data_mtime)

    return [
        # Bootstrap row containing tools at the top of the application
        toolbar_generator.get_toolbar_row(data_),
        # Bootstrap collapse containing legend
        legend_generator.get_legend_collapse(),
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
        # These are in-browser variables that Dash can treat as Inputs
        # and Outputs, in addition to more conventional Dash components
        # like HTML divs and Plotly figures. ``get-data-args`` are the
        # args used to call ``get_data`` when the underlying data
        # structure is needed.
        dcc.Store(id="get-data-args", data=get_data_args),
        # Last data file modification date. Sometimes data changes, but
        # ``get_data`` args do not. Need to rewrite cache.
        dcc.Store(id="last-data-mtime", data=last_data_mtime),
        # Clientside callbacks use the return val of ``get_data``
        # directly.
        dcc.Store(id="data", data=data_),
        # The following in-browser variables simply exist to help
        # modularize the callbacks below.
        dcc.Store(id="show-clade-defining",
                  data=get_data_args["show_clade_defining"]),
        dcc.Store(id="hidden-strains", data=get_data_args["hidden_strains"]),
        dcc.Store(id="strain-order", data=get_data_args["strain_order"]),
        dcc.Store(id="last-heatmap-cell-clicked"),
        # Used to update certain figures only when necessary
        dcc.Store(id="heatmap-x-len", data=len(data_["heatmap_x_nt_pos"])),
        dcc.Store(id="heatmap-y-strains",
                  data=len(data_["heatmap_y_strains"])),
        # Used to integrate some JS callbacks. The data values are
        # meaningless, we just need outputs to perform all clientside
        # functions.
        dcc.Store(id="make-select-lineages-modal-checkboxes-draggable"),
        dcc.Store(id="make-histogram-rel-pos-bar-dynamic"),
        dcc.Store(id="link-heatmap-cells-y-scrolling")
    ], None


@app.callback(
    output=[
        Output("get-data-args", "data"),
        Output("last-data-mtime", "data"),
        Output("data-loading", "data")
    ],
    inputs=[
        Input("show-clade-defining", "data"),
        Input("hidden-strains", "data"),
        Input("strain-order", "data"),
        Input("mutation-freq-slider", "value")
    ],
    prevent_initial_call=True
)
def update_get_data_args(show_clade_defining, hidden_strains, strain_order,
                         mutation_freq_vals):
    """Update ``get-data-args`` variables in dcc.Store.

    This is a central callback. Updating ``get-data-args`` triggers a
    change to the ``get-data-args`` variable in dcc.Store, which
    triggers multiple other callbacks to call ``read_data``, which is a
    fn that calls ``get_data`` with ``get-data-args``, and caches the
    ret val. This fn calls ``read_data`` first, so it is already cached
    before those callbacks need it.

    We also update ``last-data-mtime`` here, and ``data-loading``. In
    the case of ``data-loading``, we keep the value as ``None``, but
    returning it in this fn provides a spinner while this fn is being
    run.

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
    :return: ``get_data`` return value, last mtime across all data
        files, and ``data-loading`` children.
    :rtype: tuple[dict, float, None]
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

    args = {
        "show_clade_defining": show_clade_defining,
        "hidden_strains": hidden_strains,
        "strain_order": strain_order,
        "min_mutation_freq": min_mutation_freq,
        "max_mutation_freq": max_mutation_freq
    }

    # Update ``last-data-mtime`` too
    last_data_mtime = \
        max(path.getmtime(root) for root, _, _ in walk(REFERENCE_DATA_DIR))

    # We call ``read_data`` here, so it gets cached. Otherwise, the
    # callbacks that call ``read_data`` may do it in parallel--blocking
    # multiple processes.
    read_data(args, last_data_mtime)

    return args, last_data_mtime, None


@cache.memoize(timeout=TIMEOUT)
def read_data(get_data_args, last_data_mtime):
    """Returns and caches return value of ``get_data``.

    Why is this function necessary?

    Problem: Callbacks need access to the ``get_data`` return value,
    but moving it across the network from callback to callback greatly
    decreases performance (because it is large).

    So what are our options?

    Each callback that needs access to the ``get_data`` callback could
    call the serverside fn ``get_data`` directly, right? No need to
    move it from callback to callback? WRONG. ``get_data`` is an
    expensive step. It would be called too often, which again decreases
    performance.

    Instead, each callback calls this function, which was already
    called when ``get-data-args`` was first updated. This fn cached the
    return value, so it can now quickly supply it to the callbacks when
    necessary. And since this fn is a server-side fn too, it does not
    move the cached value over the network.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    """
    ret = get_data(
        [REFERENCE_DATA_DIR],
        show_clade_defining=get_data_args["show_clade_defining"],
        hidden_strains=get_data_args["hidden_strains"],
        strain_order=get_data_args["strain_order"],
        min_mutation_freq=get_data_args["min_mutation_freq"],
        max_mutation_freq=get_data_args["max_mutation_freq"]
    )
    return ret


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
    Output("download-file-data", "data"),
    Input("download-file-btn", "n_clicks"),
    prevent_initial_call=True
)
def trigger_download(_):
    """Send download file when user clicks download btn.

    This is a zip object of surveillance reports.

    :param _: Unused input variable that monitors when download btn is
        clicked.
    :return: Fires dash function that triggers file download
    """
    with TemporaryDirectory() as dir_name:
        reports_path = path.join(dir_name, "surveillance_reports")
        copytree(REFERENCE_SURVEILLANCE_REPORTS_DIR,
                 path.join(reports_path, "reference_surveillance_reports"))
        make_archive(reports_path, "zip", reports_path)
        return dcc.send_file(reports_path + ".zip")


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
    State({"type": "select-lineages-modal-checkbox", "index": ALL}, "id"),
    State({"type": "select-lineages-modal-checkbox", "index": ALL}, "checked"),
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_hidden_strains(_, checkbox_ids, checkbox_vals, get_data_args,
                          last_data_mtime):
    """Update ``hidden-strains`` variable in dcc.Store.

    When the OK button is clicked in the select lineages modal, the
    unchecked boxes are returned as the new ``hidden-strains`` value.

    :param _: Otherwise useless input only needed to alert us when the
        ok button in the select lineages modal was clicked.
    :param checkbox_ids: List of ids corresponding to checkboxes
    :type checkbox_ids: list[dict]
    :param checkbox_vals: List of booleans corresponding to checkboxes
        indicating whether they are checked or not.
    :type checkbox_vals: list[bool]
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: List of strains that should not be displayed by the
        heatmap or table.
    :rtype: list[str]
    :raise PreventUpdate: Hidden strains did not change, or the user
        chose to hide all strains.
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)
    old_hidden_strains = data["hidden_strains"]

    checkbox_strains = [id["index"] for id in checkbox_ids]
    hidden_strains_vals_zip_obj = \
        filter(lambda x: not x[1], zip(checkbox_strains, checkbox_vals))
    hidden_strains = [strain for (strain, _) in hidden_strains_vals_zip_obj]

    no_change = hidden_strains == old_hidden_strains
    all_hidden = checkbox_strains == hidden_strains
    if no_change or all_hidden:
        raise PreventUpdate

    return hidden_strains


@app.callback(
    Output("select-lineages-modal", "is_open"),
    Output("select-lineages-modal-body", "children"),
    Output("select-lineages-modal-loading", "children"),
    Input("open-select-lineages-modal-btn", "n_clicks"),
    Input("select-lineages-ok-btn", "n_clicks"),
    Input("select-lineages-cancel-btn", "n_clicks"),
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def toggle_select_lineages_modal(_, __, ___, get_data_args, last_data_mtime):
    """Open or close select lineages modal.

    Not only is this function in charge of opening or closing the
    select lineages modal, it is also in charge of dynamically
    populating the select lineages modal body when the modal is opened.

    This is a little slow to open, so we return
    ``select-lineages-modal-loading`` to add a spinner.

    :param _: Select lineages button in toolbar was clicked
    :param __: OK button in select lineages modal was clicked
    :param ___: Cancel button in select lineages modal was clicked
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: Boolean representing whether the select lineages modal is
        open or closed, content representing the select lineages
        modal body, and ``select-lineages-modal-loading`` children.
    :rtype: (bool, list[dbc.FormGroup])
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    ctx = dash.callback_context
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    # We only open the modal when the select lineages modal btn in the
    # toolbar is clicked.
    if triggered_prop_id == "open-select-lineages-modal-btn.n_clicks":
        modal_body = toolbar_generator.get_select_lineages_modal_body(data)
        return True, modal_body, None
    else:
        # No need to populate modal body if the modal is closed
        return False, None, None


@app.callback(
    Output({"type": "select-lineages-modal-checklist", "index": MATCH},
           "children"),
    Input({"type": "select-lineages-modal-all-btn", "index": MATCH},
          "n_clicks"),
    Input({"type": "select-lineages-modal-none-btn", "index": MATCH},
          "n_clicks"),
    State({"type": "select-lineages-modal-checklist", "index": MATCH},
          "children"),
    prevent_initial_call=True
)
def toggle_all_strains_in_select_all_lineages_modal(_, __, checkbox_rows):
    """Toggle checkboxes after user clicks "all" or "none" modal btns.

    Only the relevant checkboxes are toggled, specific to a directory,
    depending on which "all" or "none" btn the user clicked.

    :param: _: "all" btn in select lineages modal was clicked.
    :param: __: "none" btn in select lineages modal was clicked.
    :param checkbox_rows: List of rows containing checkboxes in each
        dir subsection of select lineages modal.
    :type: list
    :return: ``checkbox_rows``, but with appropriately modified checked
        vals for checkboxes.
    """
    ctx = dash.callback_context
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    triggered_prop_id_type = loads(triggered_prop_id.split(".")[0])["type"]
    ret = checkbox_rows
    # TODO the way we edit the children is hackey and could break in
    #  the future. But we're in a bit of a time crunch atm.
    if triggered_prop_id_type == "select-lineages-modal-all-btn":
        for i in range(len(ret)):
            ret[i]["props"]["children"][0]["props"]\
                ["children"]["props"]["checked"] = True
    else:
        for i in range(len(ret)):
            ret[i]["props"]["children"][0]["props"]\
                ["children"]["props"]["checked"] = False
    return ret


@app.callback(
    Output("mutation-freq-slider-col", "children"),
    Input("get-data-args", "data"),
    State("mutation-freq-slider", "marks"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_mutation_freq_slider(get_data_args, old_slider_marks,
                                last_data_mtime):
    """Update mutation frequency slider div.

    If the ``data`` dcc variable is updated, this function will
    re-render the slider if the new ``data`` variable has a different
    set of mutation frequencies.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param old_slider_marks: ``marks`` property of the current
        mutation frequency slider div.
    :type old_slider_marks: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New mutation frequency slider div, if one is needed
    :rtype: dcc.RangeSlider
    :raise PreventUpdate: Number of mutation frequencies in ``data`` is
        different than the number of mutation frequencies in the
        current slider.
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    # This is very hackey, but also very fast. I do not think this will
    # currently break anything.
    new_slider_marks = data["mutation_freq_slider_vals"]
    if len(new_slider_marks) == len(old_slider_marks):
        raise PreventUpdate

    return toolbar_generator.get_mutation_freq_slider(data)


@app.callback(
    Output("legend-collapse", "is_open"),
    Input("toggle-legend-btn", "n_clicks"),
    State("legend-collapse", "is_open"),
    prevent_initial_call=True
)
def toggle_legend_collapse(_, is_open):
    """Open or close legend view.

    :param _: Toggle legend btn was clicked
    :param is_open: Current visibility of legend
    :return: New visbility for legend; opposite of ``is_open``
    :rtype: bool
    """
    return not is_open


@app.callback(
    Output("heatmap-x-len", "data"),
    Input("get-data-args", "data"),
    State("heatmap-x-len", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def route_data_heatmap_x_update(get_data_args, old_heatmap_x_len,
                                last_data_mtime):
    """Update ``heatmap-x-len`` dcc variable when needed.

    This serves as a useful trigger for figs that only need to be
    updated when heatmap x coords change. We use the length of
    data["heatmap_x_nt_pos"] because it is faster than comparing the
    entire list, and appropriately alerts us when
    data["heatmap_x_nt_pos"] changed.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param old_heatmap_x_len: ``heatmap-x-len.data`` value
    :type old_heatmap_x_len: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New len of data["heatmap_x_nt_pos"]
    :rtype: int
    :raise PreventUpdate: If data["heatmap_x_nt_pos"] len did not
        change.
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    if old_heatmap_x_len == len(data["heatmap_x_nt_pos"]):
        raise PreventUpdate
    return len(data["heatmap_x_nt_pos"])


@app.callback(
    Output("heatmap-y-strains", "data"),
    Input("get-data-args", "data"),
    State("heatmap-y-strains", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def route_data_heatmap_y_strains_update(get_data_args, old_heatmap_y_strains,
                                        last_data_mtime):
    """Update ``heatmap-y-strains`` dcc variable when needed.

    This serves as a useful trigger for figs that only need to be
    updated when heatmap strains change.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param old_heatmap_y_strains: ``heatmap-y-strains.data`` value
    :type old_heatmap_y_strains: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New len of data["heatmap_y_strains"]
    :rtype: int
    :raise PreventUpdate: If data["heatmap_y_strains"] len did not
        change.
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    if old_heatmap_y_strains == data["heatmap_y_strains"]:
        raise PreventUpdate
    return data["heatmap_y_strains"]


@app.callback(
    Output("heatmap-strains-axis-fig", "figure"),
    Output("heatmap-strains-axis-fig", "style"),
    Output("heatmap-strains-axis-inner-container", "style"),
    Output("heatmap-strains-axis-outer-container", "style"),
    Input("heatmap-y-strains", "data"),
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_heatmap_strains_axis_fig(_, get_data_args, last_data_mtime):
    """Update heatmap strains axis fig and containers.

    We need to update style because attributes may change due to
    uploaded strains.

    :param _: Heatmap strains updated
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New heatmap strains axis fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    strain_axis_fig = heatmap_generator.get_heatmap_strains_axis_fig(data)
    strain_axis_style = \
        {"height": data["heatmap_cells_fig_height"],
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
    return (strain_axis_fig, strain_axis_style, inner_container_style,
            outer_container_style)


@app.callback(
    Output("heatmap-sample-size-axis-fig", "figure"),
    Output("heatmap-sample-size-axis-fig", "style"),
    Output("heatmap-sample-size-axis-inner-container", "style"),
    Output("heatmap-sample-size-axis-outer-container", "style"),
    Input("heatmap-y-strains", "data"),
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_heatmap_sample_size_axis_fig(_, get_data_args, last_data_mtime):
    """Update heatmap sample size axis fig and containers.

    We need to update style because attributes may change due to
    uploaded strains.

    :param _: Heatmap strains updated
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New heatmap sample size axis fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    sample_size_axis_fig = \
        heatmap_generator.get_heatmap_sample_size_axis_fig(data)
    sample_size_axis_style = \
        {"height": data["heatmap_cells_fig_height"],
         "width": "101%",
         "marginBottom": -data["heatmap_cells_container_height"]}
    inner_container_style = {
        "height": "100%",
        "overflowX": "scroll",
        "overflowY": "scroll",
        "marginRight": -50,
        "paddingRight": 50,
        "marginBottom":
            -data["heatmap_cells_container_height"]-50,
        "paddingBottom":
            data["heatmap_cells_container_height"]+50
    }
    outer_container_style = {
        "height": data["heatmap_cells_container_height"],
        "overflow": "hidden"
    }
    return (sample_size_axis_fig, sample_size_axis_style,
            inner_container_style, outer_container_style)


@app.callback(
    Output("heatmap-gene-bar-fig", "figure"),
    Output("heatmap-gene-bar-fig", "style"),
    Input("heatmap-x-len", "data"),
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_heatmap_gene_bar_fig(_, get_data_args, last_data_mtime):
    """Update heatmap gene bar fig.

    We need to update style because width might have changed due to
    added nt positions in data.

    :param _: Heatmap cells fig updated
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New heatmap gene bar fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    gene_bar_fig = heatmap_generator.get_heatmap_gene_bar_fig(data)
    gene_bar_style = {"width": data["heatmap_cells_fig_width"]}
    return gene_bar_fig, gene_bar_style


@app.callback(
    Output("heatmap-nt-pos-axis-fig", "figure"),
    Output("heatmap-nt-pos-axis-fig", "style"),
    Input("heatmap-x-len", "data"),
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_heatmap_nt_pos_axis_fig(_, get_data_args, last_data_mtime):
    """Update heatmap nt pos axis fig.

    We need to update style because width might have changed due to
    added nt positions in data.

    :param _: Heatmap cells fig updated
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New heatmap nt pos x-axis fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    nt_pos_x_axis_fig = heatmap_generator.get_heatmap_nt_pos_axis_fig(data)
    nt_pos_x_axis_style = {"width": data["heatmap_cells_fig_width"]}
    return nt_pos_x_axis_fig, nt_pos_x_axis_style


@app.callback(
    Output("heatmap-aa-pos-axis-fig", "figure"),
    Output("heatmap-aa-pos-axis-fig", "style"),
    Input("heatmap-x-len", "data"),
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_heatmap_aa_pos_axis_fig(_, get_data_args, last_data_mtime):
    """Update heatmap amino acid position axis fig.

    We need to update style because width might have changed due to
    added nt positions in data.

    :param _: Heatmap cells fig updated
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New heatmap amino acid position x-axis fig and style
    :rtype: (plotly.graph_objects.Figure, dict)
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    aa_pos_x_axis_fig = heatmap_generator.get_heatmap_aa_pos_axis_fig(data)
    aa_pos_x_axis_style = {"width": data["heatmap_cells_fig_width"]}
    return aa_pos_x_axis_fig, aa_pos_x_axis_style


@app.callback(
    Output("histogram-top-row-div", "children"),
    Input("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_histogram(get_data_args, last_data_mtime):
    """Update histogram top row div.

    When the ``data`` variable in the dcc.Store is updated, the top row
    in the histogram view is updated to reflect the new data. This
    includes the actual histogram bars, and the y axis.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New histogram figure corresponding to new data
    :rtype: plotly.graph_objects.Figure
    """
    data = read_data(get_data_args, last_data_mtime)
    return histogram_generator.get_histogram_top_row(data)


@app.callback(
    Output("heatmap-cells-fig", "figure"),
    Output("heatmap-cells-fig", "style"),
    Output("heatmap-cells-inner-container", "style"),
    Output("heatmap-cells-outer-container", "style"),
    Output("data-loading", "children"),
    Input("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_heatmap_cells_fig(get_data_args, last_data_mtime):
    """Update heatmap cells fig, style, and containers.

    This is the fig with the heatmap cells and x axis. We return style
    because attributes may need to change due to changes in data.

    We also update ``data-loading``. We keep the value as ``None``,
    but returning it in this fn provides a spinner while this fn is
    being run.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New heatmap cells fig, associated styles, and
        ``data-loading`` children.
    :rtype: Tuple(plotly.graph_objects.Figure, dict, dict, dict, None)
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

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
            outer_container_style, None)


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
    State("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def toggle_mutation_details_modal(click_data, _, get_data_args,
                                  last_data_mtime):
    """Open or close mutation details modal.

    Not only is this function in charge of opening or closing the
    mutation details modal, it is also in charge of dynamically
    populating the mutation details modal body when the modal is
    opened.

    :param click_data: ``last-heatmap-cell-clicked`` in-browser
        variable value.
    :type click_data: dict
    :param _: Close button in mutation details modal was clicked
    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: Boolean representing whether the mutation details modal is
        open or closed, mutation details modal header, and mutation
        details body.
    :rtype: (bool, str, dbc.ListGroup)"""
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

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
        Input("get-data-args", "data"),
        Input("last-heatmap-cell-clicked", "data"),
    ],
    state=[
        State("last-data-mtime", "data")
    ],
    prevent_initial_call=True
)
def update_table(get_data_args, click_data, last_data_mtime):
    """Update table figure.

    When the ``data`` variable in the dcc.Store is updated, the table
    figure is updated as well. The table figure is also updated when
    the user clicks a heatmap cell. If no cell was clicked, a default
    strain is shown.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param click_data: ``last-heatmap-cell-clicked`` in-browser
        variable value.
    :type click_data: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: New table figure corresponding to new data, or user
        selected strain.
    :rtype: plotly.graph_objects.Figure
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)

    ctx = dash.callback_context
    triggered_prop_id = ctx.triggered[0]["prop_id"]
    if triggered_prop_id == "get-data-args.data":
        table_strain = data["heatmap_y_strains"][0]
    else:
        table_strain = data["heatmap_y_strains"][click_data["points"][0]["y"]]

    # If you click a strain, but then hide it, this condition stops
    # things from breaking.
    if table_strain in data["hidden_strains"]:
        table_strain = data["heatmap_y_strains"][0]

    return table_generator.get_table_fig(data, table_strain)


@app.callback(
    Output("data", "data"),
    Input("get-data-args", "data"),
    State("last-data-mtime", "data"),
    prevent_initial_call=True
)
def update_data(get_data_args, last_data_mtime):
    """Update ``data`` in dcc.Store.

    The output is only used in clientside callbacks. It is too large to
    transport over the network.

    :param get_data_args: Args for ``get_data``
    :type get_data_args: dict
    :param last_data_mtime: Last mtime across all data files
    :type last_data_mtime: float
    :return: ``get_data`` return val
    :rtype: dict
    """
    # Current ``get_data`` return val
    data = read_data(get_data_args, last_data_mtime)
    return data


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
    State("strain-order", "data"),
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
    Input("heatmap-strains-axis-fig", "figure"),
    Input("heatmap-sample-size-axis-fig", "figure"),
    Input("heatmap-cells-fig", "figure")
)

if __name__ == "__main__":
    # Serve ``app``
    app.run_server(debug=False, host='0.0.0.0')
