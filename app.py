"""Entry point of the codebase.

This is the Python script that is run to launch the visualization
application.

Unfortunately, all callbacks must be located in this file, and Dash
does not allow multiple callbacks to share outputs, so the callbacks
are not as organized as I would like. I have tried my best, but please
read the function docstrings and comments if you are confused.
"""

from base64 import b64decode

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
from dash.dependencies import ALL, Input, Output
import dash_html_components as html

from data_parser import get_data
import div_generator
import heatmap_generator
import table_generator

app = dash.Dash(__name__,
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
    We do not care about its value, we just use it to indicate the page
    was loaded.

    Populating the initial layout with a callback, instead of in the
    global scope, prevents the application from breaking on page
    reload. Dash is stateless, so it does not recalculate global
    variables on page refreshes after the application is first deployed
    to a server. So new data between page reloads may not be displayed
    if you populate the initial layout in the global scope.
    """
    hidden_strains = []
    data_ = get_data(["data", "user_data"], hidden_strains=hidden_strains)
    return [
        html.Div(div_generator.get_toolbar_row_div(data_)),
        html.Div(div_generator.get_heatmap_row_div(data_)),
        html.Div(div_generator.get_table_row_div(data_)),
        # These are in-browser variables that Dash can treat as Inputs and
        # Outputs, in addition to more conventional Dash components like
        # HTML divs and Plotly figures. ``data`` is the data used to
        # generate the heatmap and table. A bit confusing, but dcc.Store
        # variables have data attributes. So ``data`` has a ``data``
        # attribute.
        dcc.Store(id="data", data=data_),
        # The following in-browser variables simply exist to help
        # modularize the callbacks below, by alerting us when ``data`` is
        # changed.
        dcc.Store(id="show-clade-defining"),
        dcc.Store(id="new-upload"),
        dcc.Store(id="hidden-strains", data=hidden_strains)
    ]


@app.callback(
    Output("data", "data"),
    inputs=[
        Input("show-clade-defining", "data"),
        Input("new-upload", "data"),
        Input("hidden-strains", "data")
    ],
    prevent_initial_call=True
)
def update_data(show_clade_defining, new_upload, hidden_strains):
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
    :return: ``get_data`` return value
    :rtype: dict
    """
    ctx = dash.callback_context
    if ctx.triggered[0]["prop_id"] == "new-upload.data":
        if new_upload["status"] == "error":
            return dash.dash.no_update
    return get_data(["data", "user_data"],
                    clade_defining=show_clade_defining,
                    hidden_strains=hidden_strains)


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
    :type show_clade_defining: list
    :return: True if clade defining mutations switch is switched on
    :rtype: bool
    """
    return len(switches_value) > 0


@app.callback(
    Output("new-upload", "data"),
    Input("upload-file", "contents"),
    Input("upload-file", "filename"),
    prevent_initial_call=True
)
def update_new_upload(file_contents, filename):
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
    :return: Dictionary describing upload attempt
    :rtype: dict
    """
    data_ = get_data(["data", "user_data"])
    # TODO more thorough validation, maybe once we finalize data
    #  standards.
    new_strain, ext = filename.rsplit(".", 1)
    if ext != "tsv":
        status = "error"
        msg = "Filename must end in \".tsv\"."
    elif new_strain in data_["heatmap_y"]:
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
    Output("hidden-strains", "data"),
    inputs=[
        Input({"type": "hide-strain-dropdown-item", "index": ALL}, "n_clicks"),
        Input({"type": "hide-strain-dropdown-item", "index": ALL}, "children"),
        Input({"type": "hide-strain-dropdown-item", "index": ALL}, "active")
    ],
    prevent_initial_call=True
)
def update_hidden_strains(n_clicks_list, strain_list, active_list):
    """Update ``hidden-strains`` variable in dcc.Store.

    When a strain in the hide strains dropdown menu is activated, it is
    added to ``hidden-strains``. When it is unactivated, it is removed.
    Hidden strains are not displayed in the heatmap or table.
    TODO: probably going to take a different approach to this, with a
     more complex dropdown that allows you to reorder the heatmap and
     select reference strains for clade defining mutations.

    :param n_clicks_list: List of elements corresponding to each
        dropdown menu item, with ``None`` for every element except the
        one that was clicked, which has a ``1`` value.
    :type n_clicks_list: list
    :param strain_list: List of strains corresponding to each dropdown
        menu item.
    :type strain_list: list[str]
    :param active_list: List of ``True`` or ``False`` values
        corresponding to ``active`` attribute of each dropdown menu
        item.
    :type active_list: list[bool]
    :return: List of strains that should not be displayed by the
        heatmap or table, and should be marked active in the hide
        strain dropdown menu.
    :rtype: list[str]
    """
    hidden_strains = []
    for i, strain in enumerate(strain_list):
        if n_clicks_list[i] and not active_list[i]:
            hidden_strains.append(strain)
        elif not n_clicks_list[i] and active_list[i]:
            hidden_strains.append(strain)
    return hidden_strains


@app.callback(
    Output("dialog-col", "children"),
    Input("new-upload", "data"),
    prevent_initial_call=True
)
def update_dialog_col(new_upload):
    """Update ``dialog-col`` div in toolbar.

    This function shows an error alert when there was an unsuccessful
    upload by the user.

    :param new_upload: ``update_new_upload`` return value
    :type new_upload: dict
    :return: Dash Bootstrap Components alert if new_upload describes an
        unsuccessfully uploaded file.
    :rtype: dbc.Alert
    """
    if new_upload["status"] == "error":
        return dbc.Alert(new_upload["msg"],
                         color="danger",
                         className="mb-0 p-1 d-inline-block")
    else:
        return None


@app.callback(
    Output("hide-dropdown-btn", "children"),
    Input("data", "data"),
    prevent_initial_call=True
)
def update_hide_dropdown_btn(data):
    """Update ``hide_dropdown_btn`` div in toolbar.

    When the ``data`` variable in the dcc.Store is updated, the
    dropdown will show the updated list of strains.

    :param data: ``get_data`` return value, transported here by
        ``update_data``.
    :type data: dict
    :return: List of Dash Bootstrap Components dropdown menu items
        corresponding to strains in data.
    :rtype: list[dbc.DropdownMenuItem]
    """
    return div_generator.get_hide_strains_component_children(data)


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
    if table_strain not in data["heatmap_y"]:
        table_strain = data["heatmap_y"][0]

    return table_generator.get_table_fig(data, table_strain)


if __name__ == "__main__":
    app.run_server(debug=True)
