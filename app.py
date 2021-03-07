"""TODO..."""

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from data_parser import get_data
import heatmap_generator
import table_generator

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

data = get_data()

heatmap_row = html.Div([
    dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-left-fig",
                    figure=heatmap_generator.get_heatmap_left_fig(data)
                ),
                style={"width": "90vw", "overflowX": "hidden"}
            ),
            width=1
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-center-fig",
                    figure=heatmap_generator.get_heatmap_center_fig(data)
                ),
                style={"overflowX": "scroll"}
            ),
            width=10
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(
                    id="heatmap-right-fig",
                    figure=heatmap_generator.get_heatmap_right_fig(data)
                ),
            ),
            width=1
        ),
    ], no_gutters=True),
])

table_row = html.Div([
    dbc.Row(
        dbc.Col(
            dcc.Graph(
                id="table",
                figure=
                table_generator.get_table_fig(data,data["heatmap_y"][0])
            )
        ),
    )
])

app.layout = dbc.Container([
    heatmap_row,
    table_row
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
