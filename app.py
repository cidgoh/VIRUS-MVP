"""TODO..."""

import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from data_parser import get_data
import div_generator
import table_generator

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

data = get_data()

app.layout = dbc.Container([
    div_generator.get_heatmap_row_div(data),
    div_generator.get_table_row_div(data)
], fluid=True)

@app.callback(
     output=Output('table', 'figure'),
     inputs=[Input('heatmap-center-fig', 'clickData')])
def display_table(clickData):
    if clickData is None:
        table_strain = data["heatmap_y"][0]
    else:
        table_strain = clickData["points"][0]["y"]
    ret = table_generator.get_table_fig(data, table_strain)
    return ret


if __name__ == "__main__":
    app.run_server(debug=True)
