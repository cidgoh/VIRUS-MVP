"""TODO..."""

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

from data_parser import get_data
import heatmap_generator

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
            dcc.Graph(id="table")
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
    header_vals = ["pos", "ref", "alt", "alt_freq"]

    if clickData is None:
        table_strain = data["heatmap_y"][0]
    else:
        table_strain = clickData["points"][0]["y"]

    table_obj = go.Table(
        header={"values": ["<b>%s</b>" % e for e in header_vals],
                "line_color": "black",
                "fill_color": "white",
                "height": 32,
                "font": {"size": 18}
                },
        cells={"values": data["tables"][table_strain],
               "line_color": "black",
               "fill_color": "white",
               "height": 32,
               "font": {"size": 18}
               }
    )
    table_fig = go.Figure(table_obj)
    table_fig.update_layout(title={
        "text": table_strain,
        "font": {"size": 24}
    })
    return table_fig


if __name__ == "__main__":
    app.run_server(debug=True)
