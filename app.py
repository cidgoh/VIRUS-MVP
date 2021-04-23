"""Entry point of the codebase.

This is the Python script that is run to launch the visualization
application.
"""

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from data_parser import get_data
import div_generator
import heatmap_generator
import table_generator

app = dash.Dash(__name__,
                # We can use bootstrap CSS.
                # https://bit.ly/3tMqY0W for details.
                external_stylesheets=[dbc.themes.BOOTSTRAP])

data = get_data("data")
clade_defining_mutations_data = get_data("clade_defining_mutations_data")

app.layout = dbc.Container([
    div_generator.get_toolbar_row_div(),
    div_generator.get_heatmap_row_div(data),
    div_generator.get_table_row_div(data)
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
        return table_generator \
            .get_table_fig(clade_defining_mutations_data, table_strain)
    else:
        return table_generator.get_table_fig(data, table_strain)


@app.callback(
    Output("heatmap-center-fig", "figure"),
    Input("clade-defining-mutations-switch", "value"),
    prevent_initial_call=True
)
def on_form_change(switches_value):
    """Callback function for updating heatmap.

    The heatmap is updated when the clade defining mutations switch is
    toggled.

    Only the center figure in the heatmap is updated.

    :param switches_value: Information on clade defining mutations
        switch.
    :type switches_value: dict
    :return: Center heatmap figure to show
    :rtype: plotly.graph_objects.Figure
    """
    if len(switches_value) > 0:
        return heatmap_generator \
            .get_heatmap_center_fig(clade_defining_mutations_data)
    else:
        return heatmap_generator.get_heatmap_center_fig(data)


if __name__ == "__main__":
    app.run_server(debug=True)
