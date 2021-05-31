"""Entry point of the codebase.

This is the Python script that is run to launch the visualization
application.

Unfortunately, all callbacks must be located in this file, and Dash
does not allow multiple callbacks to share outputs, so the callbacks
are not as organized as I would like. I have tried my best, but please
read the function docstrings and comments if you are confused.
"""

from base64 import b64decode
from time import sleep

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import ALL, ClientsideFunction, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_html_components as html

from data_parser import get_data, parse_gff3_file
import toolbar_generator
import heatmap_generator
import histogram_generator
import table_generator

app = dash.Dash(__name__,
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
                suppress_callback_exceptions=True)

app.layout = dbc.Container(
    # In-browser variable only used when page is first loaded. This
    # variable helps us avoid global variables, which cause problems on
    # refresh with Dash, as Dash is stateless.
    dcc.Store("first-launch"),
    fluid=True,
    id="main-container")


@app.callback(
    Output("main-container", "children"),
    Input("first-launch", "data")
)
def launch_app(_):
    """Generate initial layout on page load.

    ``first-launch`` should only receive input when the page is loaded.
    We do not care about its value, as we just use it to indicate the
    page was loaded.

    Populating the initial layout with a callback, instead of in the
    global scope, prevents the application from breaking on page
    reload. Dash is stateless, so it does not recalculate global
    variables on page refreshes after the application is first deployed
    to a server. So new data between page reloads may not be displayed
    if you populate the initial layout in the global scope.
    """
    gff3_annotations = parse_gff3_file("gff3_annotations.tsv")
    data_ = get_data(["reference_data", "user_data"], gff3_annotations)
    return [
        html.Div(toolbar_generator.get_toolbar_row_div(data_)),
        html.Div(heatmap_generator.get_heatmap_row_div(data_)),
        html.Div(histogram_generator.get_histogram_row_div(data_)),
        html.Div(table_generator.get_table_row_div(data_)),
        html.Div(toolbar_generator.get_select_lineages_modal()),
        # These are in-browser variables that Dash can treat as Inputs and
        # Outputs, in addition to more conventional Dash components like
        # HTML divs and Plotly figures. ``data`` is the data used to
        # generate the heatmap and table. A bit confusing, but dcc.Store
        # variables have data attributes. So ``data`` has a ``data``
        # attribute.
        dcc.Store(id="gff3-annotations", data=gff3_annotations),
        dcc.Store(id="data", data=data_),
        # The following in-browser variables simply exist to help
        # modularize the callbacks below, by alerting us when ``data``
        # should be changed.
        dcc.Store(id="show-clade-defining"),
        dcc.Store(id="new-upload"),
        dcc.Store(id="hidden-strains"),
        dcc.Store(id="strain-order"),
        # Used to integrate JQuery UI drag and drop on client side. The
        # data value is meaningless, we just need an output to perform
        # the clientside function. TODO
        dcc.Store(id="make-select-lineages-modal-checkboxes-draggable"),
        dcc.Store(id="foo"),
    ]


@app.callback(
    Output("data", "data"),
    inputs=[
        Input("show-clade-defining", "data"),
        Input("new-upload", "data"),
        Input("hidden-strains", "data"),
        Input("strain-order", "data"),
        Input("mutation-freq-slider", "value")
    ],
    state=[
        State("gff3-annotations", "data")
    ],
    prevent_initial_call=True
)
def update_data(show_clade_defining, new_upload, hidden_strains, strain_order,
                mutation_freq_vals, gff3_annotations):
    """Update ``data`` variable in dcc.Store.

    This is a central callback. It triggers a change to the ``data``
    variable in dcc.Store, which triggers cascading changes in several
    divs. This function receives multiple inputs, corresponding to
    different ways the ``data`` variable could be changed.

    :param show_clade_defining: ``update_show_clade-defining`` return
        value.
    :type show_clade_defining: bool
    :param new_upload: ``update_new_upload`` return value
    :type new_upload: dict
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
    """
    # Do not update if a new upload triggered this function, and that
    # new upload failed.
    triggers = [x["prop_id"] for x in dash.callback_context.triggered]
    if "new-upload.data" in triggers:
        if new_upload["status"] == "error":
            raise PreventUpdate

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

    return get_data(["reference_data", "user_data"],
                    gff3_annotations,
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
    Output("new-upload", "data"),
    Input("upload-file", "contents"),
    Input("upload-file", "filename"),
    State("data", "data"),
    prevent_initial_call=True
)
def update_new_upload(file_contents, filename, old_data):
    """Update ``new_upload`` variable in dcc.Store.

    If a valid file is uploaded, it will be written to ``user_data``.
    But regardless of whether a valid file is uploaded, this function
    will return a dict describing the name of the file the user
    attempted to upload, and status of upload.

    :param file_contents: Contents of uploaded file, formatted by Dash
        into a base64 string.
    :type file_contents: str
    :param filename: Name of uploaded file
    :type filename: str
    :param old_data: ``get_data`` return value; current value for
        ``data`` variable.
    :type old_data: dict
    :return: Dictionary describing upload attempt
    :rtype: dict
    """
    # TODO more thorough validation, maybe once we finalize data
    #  standards.
    new_strain, ext = filename.rsplit(".", 1)
    if ext != "tsv":
        status = "error"
        msg = "Filename must end in \".tsv\"."
    elif new_strain in old_data["heatmap_y"]:
        status = "error"
        msg = "Filename must not conflict with existing voc."
    else:
        # Dash splits MIME type and the actual str with a comma
        _, base64_str = file_contents.split(",")
        # File gets written to ``user_data`` folder
        # TODO: eventually replace with database
        with open("user_data/" + filename, "w") as fp:
            tsv_str_bytes = b64decode(base64_str)
            tsv_str_utf8 = tsv_str_bytes.decode("utf-8")
            fp.write(tsv_str_utf8)
        status = "ok"
        msg = ""
    return {"filename": filename, "msg": msg, "status": status}


@app.callback(
    Output("dialog-col", "children"),
    Input("new-upload", "data"),
    Input("mutation-freq-slider", "marks"),
    prevent_initial_call=True
)
def update_dialog_col(new_upload, _):
    """Update ``dialog-col`` div in toolbar.

    This function shows an error alert when there was an unsuccessful
    upload by the user, or the mutation frequency slider was
    re-rendered. In a hackey way, this function triggers
    ``hide_dialog_col``, which hides the dialog col after some time.

    :param new_upload: ``update_new_upload`` return value
    :type new_upload: dict
    :param _: Unused input variable that allows re-rendering of the
        mutation frequency slider to trigger this function.
    :return: Dash Bootstrap Components alert if new_upload describes an
        unsuccessfully uploaded file.
    :rtype: dbc.Alert
    """
    triggers = [x["prop_id"] for x in dash.callback_context.triggered]

    if "new-upload.data" in triggers and new_upload["status"] == "error":
        return dbc.Fade(
            dbc.Alert(new_upload["msg"],
                      color="danger",
                      className="mb-0 p-1 d-inline-block"),
            id="temp-dialog-col",
            style={"transition": "all 500ms linear 0s"}
        )
    elif "mutation-freq-slider.marks" in triggers:
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
    """
    # Merge list of lists into single list. I got it from:
    # https://stackoverflow.com/a/716761/11472358.
    checked_strains = [j for i in values for j in i]

    all_strains = data["all_strains"]
    hidden_strains = []
    for strain in all_strains:
        if strain not in checked_strains:
            hidden_strains.append(strain)

    # Do not update if the hidden strains did not change, or if the
    # user chose to hide all strains.
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
    """
    # This is very hackey, but also very fast. We simply check if the
    # number of mutation frequencies in the updated ``data`` is
    # different than the number of mutation frequencies in the current
    # slider. I do not think this will currently break anything.
    new_slider_marks = data["mutation_freq_slider_vals"]
    if len(new_slider_marks) == len(old_slider_marks):
        raise PreventUpdate

    return toolbar_generator.get_mutation_freq_slider(data)


@app.callback(
    Output("heatmap-left-fig", "figure"),
    Output("heatmap-center-fig", "figure"),
    Output("heatmap-right-fig", "figure"),
    Output("heatmap-center-fig", "style"),
    Input("data", "data"),
    prevent_initial_call=True
)
def update_heatmap(data):
    """Update heatmap figures and center figure style.

    When the ``data`` variable in the dcc.Store is updated, the
    left, center, and right figures of the heatmap are updated as well.
    We update the figures instead of the whole row because it less
    computationally expensive. We must also update the style of the
    center figure due to a weirdness between Python Plotly and
    JavaScript Plotly described in ``div_generator``.

    :param data: ``get_data`` return value, transported here by
        ``update_data``.
    :type data: dict
    :return: Left, center, and right heatmap figures, and center figure
        style.
    :rtype: (plotly.graph_objects.Figure, plotly.graph_objects.Figure,
        plotly.graph_objects.Figure, dict)
    """
    left_fig = heatmap_generator.get_heatmap_left_fig(data)
    center_fig = heatmap_generator.get_heatmap_center_fig(data)
    right_fig = heatmap_generator.get_heatmap_right_fig(data)
    center_style = {"width": len(data["heatmap_x"]) * 25}
    return left_fig, center_fig, right_fig, center_style


@app.callback(
    Output("histogram", "figure"),
    Input("data", "data"),
    prevent_initial_call=True
)
def update_histogram(data):
    """Update histogram figure.

    When the ``data`` variable in the dcc.Store is updated, the
    histogram figure is updated to reflect the new data.

    :param data: ``get_data`` return value, transported here by
    :type data: dict
    :return: New histogram figure corresponding to new data
    :rtype: plotly.graph_objects.Figure
    """
    return histogram_generator.get_histogram_fig(data)


@app.callback(
    Output("table", "figure"),
    inputs=[
        Input("data", "data"),
        Input("heatmap-center-fig", "clickData"),
    ],
    prevent_initial_call=True
)
def update_table(data, click_data):
    """Update table figure.

    When the ``data`` variable in the dcc.Store is updated, the table
    figure is updated as well. The table figure is also updated when
    the user clicks a heatmap cell. If no cell was clicked, a default
    strain is shown.
    TODO only update when user clicks cell in new row

    :param data: ``get_data`` return value, transported here by
    :type data: dict
    :param click_data: Dictionary describing cell in heatmap center
        figure that the user clicked.
    :type click_data: dict
    :return: New table figure corresponding to new data, or user
        selected strain.
    :rtype: plotly.graph_objects.Figure
    """
    if click_data is None:
        table_strain = data["heatmap_y"][0]
    else:
        table_strain = click_data["points"][0]["y"]

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
        function_name="foo"
    ),
    Output("foo", "data"),
    Input("histogram", "id")
)

if __name__ == "__main__":
    app.run_server(debug=True)
