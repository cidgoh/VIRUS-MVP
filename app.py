"""TODO..."""

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from data_parser import get_data
import div_generator
import heatmap_generator
import table_generator

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

data = get_data()

app.layout = dbc.Container([
    div_generator.get_clade_defining_mutations_switch(),
    div_generator.get_heatmap_row_div(data),
    div_generator.get_table_row_div(data)
], fluid=True)


@app.callback(
    Output('table', 'figure'),
    Input('heatmap-center-fig', 'clickData'),
    prevent_initial_call=True
)
def display_table(clickData):
    """TODO..."""
    table_strain = clickData["points"][0]["y"]
    ret = table_generator.get_table_fig(data, table_strain)
    return ret


@app.callback(
    Output("heatmap-center-fig", "figure"),
    Input("clade-defining-mutations-switch", "value"),
    prevent_initial_call=True
)
def on_form_change(switches_value):
    if len(switches_value) >0:
        return heatmap_generator.get_heatmap_center_fig(data)
    else:
        return heatmap_generator.get_heatmap_center_fig(data)


if __name__ == "__main__":
    app.run_server(debug=True)
