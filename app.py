"""Entry point of the codebase.

This is the Python script that is run to launch the visualization
application.
"""

from base64 import b64decode

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_html_components as html

from data_parser import get_data
import div_generator
import table_generator

app = dash.Dash(__name__,
                # We can use bootstrap CSS.
                # https://bit.ly/3tMqY0W for details.
                external_stylesheets=[dbc.themes.COSMO])

data = get_data(["data"])

app.layout = dbc.Container([
    html.Div(div_generator.get_toolbar_row_div(data)),
    html.Div(div_generator.get_heatmap_row_div(data), id="heatmap-fig"),
    html.Div(div_generator.get_table_row_div(data))
], fluid=True)


@app.callback(
    Output("table", "figure"),
    inputs=[
        Input("heatmap-center-fig", "clickData"),
        Input("clade-defining-mutations-switch", "value")
    ],
    prevent_initial_call=True
)
def display_table(click_data, switches_value):
    """Callback function for updating table.

    The table is updated when a heatmap cell is clicked, or the clade
    defining mutations switch is toggled.

    :param click_data: Information on heatmap cell clicked
    :type click_data: dict
    :param switches_value: Information on clade defining mutations
        switch.
    :type switches_value: dict
    :return: Table figure to show
    :rtype: plotly.graph_objects.Figure
    """
    if click_data is None:
        table_strain = data["heatmap_y"][0]
    else:
        table_strain = click_data["points"][0]["y"]

    if len(switches_value) > 0:
        data_to_use = get_data(["data"], clade_defining=True)
    else:
        data_to_use = get_data(["data"], clade_defining=False)

    return table_generator.get_table_fig(data_to_use, table_strain)

@app.callback(
    Output("heatmap-fig", "children"),
    Output("dialog-col", "children"),
    Input("clade-defining-mutations-switch", "value"),
    Input("upload-file", "contents"),
    Input("upload-file", "filename"),
    prevent_initial_call=True
)
def update_heatmap(switches_value, file_contents, filename):
    """Callback function mainly for updating heatmap.

    TODO: this docstring will probably need to be updated when I am
     done tinkering.

    Dash does not allow a many-to-one mapping of callback functions and
    outputs, so this function will update the heatmap in a variety of
    ways, given a variety of inputs.

    When the clade definitions mutation switch is toggled, the heatmap
    is updated to show the appropriate mutations.

    When a file is uploaded, the heatmap is updated to show an
    additional row.

    This function also updates the dialog col in the top row div.
    Ideally, this col should communicate something about updates to the
    heatmap.

    :param switches_value: ``[1]`` or ``[0]`` is clade defining
        mutations switch is toggled on or off respectively.
    :type switches_value: list
    :param file_contents: base64 encoded string of uploaded file
        contents.
    :type file_contents: str
    :param filename: Name of uploaded file
    :type filename: str
    :return: New dash bootstrap components row containing heatmap
        figures, and maybe the dialog col in the top row div.
    :rtype: (dbc.Row, Any)
    """
    dialog_col = None
    if file_contents and filename:
        # TODO more thorough validation, maybe once we finalize data
        #  standards.
        new_strain, ext = filename.rsplit(".", 1)
        if ext != "tsv":
            dialog_col = dbc.Alert("Filename must end in \".tsv\".",
                                   color="danger",
                                   className="mb-0 p-1 d-inline-block")
        elif new_strain in data["heatmap_y"]:
            dialog_col = dbc.Alert("Filename must not conflict with existing "
                                   "voc.",
                                   color="danger",
                                   className="mb-0 p-1 d-inline-block")
        else:
            # Dash splits MIME type and the actual str with a comma
            _, base64_str = file_contents.split(",")
            # File gets written to user_data folder
            # TODO: eventually replace with database
            with open("user_data/" + filename, "w") as fp:
                tsv_str_bytes = b64decode(base64_str)
                tsv_str_utf8 = tsv_str_bytes.decode("utf-8")
                fp.write(tsv_str_utf8)
            dialog_col = dbc.Alert("File uploaded.",
                                   color="success",
                                   className="mb-0 p-1 d-inline-block")

    if len(switches_value) > 0:
        data_to_use = get_data(["data"], clade_defining=True)
    else:
        data_to_use = get_data(["data"], clade_defining=False)

    heatmap_row_div = div_generator.get_heatmap_row_div(data_to_use)

    return heatmap_row_div, dialog_col


if __name__ == "__main__":
    app.run_server(debug=True)
