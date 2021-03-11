"""TODO..."""

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import csv

from data_parser import get_data
import div_generator
import heatmap_generator
import table_generator
from collections import OrderedDict
from plotly.subplots import make_subplots

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

data = get_data("data")
clade_defining_mutations_data = get_data("clade_defining_mutations_data")

app.layout = dbc.Container([
    div_generator.get_clade_defining_mutations_switch(),
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
    """TODO..."""
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
    """TODO..."""
    if len(switches_value) > 0:
        return heatmap_generator \
            .get_heatmap_center_fig(clade_defining_mutations_data)
    else:
        return heatmap_generator.get_heatmap_center_fig(data)


if __name__ == "__main__":
    app.run_server(debug=True)
