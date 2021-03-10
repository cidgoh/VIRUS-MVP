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

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.4, 0.6], vertical_spacing=0.05)

# bars_dict = OrderedDict()
#
# with open("reference_genome_map.tsv") as fp:
#     reader = csv.DictReader(fp, delimiter="\t")
#     for row in reader:
#         region = row["region"]
#         start = int(row["start"])
#         end = int(row["end"])
#         closest_x = None
#         for x in data["heatmap_x"]:
#             if start <= x <= end:
#                 closest_x = x
#         if closest_x is not None:
#             bars_dict[region] = closest_x
#
# bar_objs = []
# color = True
# for region in reversed(bars_dict):
#     bar_obj = go.Bar(
#         x=[bars_dict[region]],
#         y=[1],
#         orientation="h",
#         marker={
#             "color": "lightgrey" if color else "white",
#             "line": {"color": "black", "width": 2}
#         },
#         text=[region],
#         textposition="inside",
#         showlegend=False,
#         hoverinfo="none"
#     )
#     bar_objs.append(bar_obj)
#     color = not color

# fig = go.Figure(bar_objs)

# for bar_obj in bar_objs:
#     fig.add_trace(bar_obj, row=1, col=1)

fig.update_layout(
    shapes=[
        {
            "type": "rect",
            "xref": "x1",
            "yref": "y1",
            "x0": -0.5,
            "x1": 1.5,
            "y0": 0,
            "y1": 1,
        }
    ]
)
heatmap_obj = heatmap_generator.get_heatmap_center_base_obj(data)
# fig.add_trace(heatmap_obj, row=1, col=1)
fig.add_trace(heatmap_obj, row=2, col=1)
#
fig.update_layout(barmode="overlay", font={"size": 18})
fig.update_xaxes(type="category", categoryorder="array", categoryarray=data["heatmap_x"])
# fig.update_xaxes(type="category")
# fig.update_yaxes(visible=False)
fig.update_layout(margin={
    # "l": 0,
    "r": 0,
    "t": 0,
    "pad": 0
})
fig.update_layout(width=len(data["heatmap_x"]) * 25, autosize=False)
# fig.update_layout(plot_bgcolor="white")
# fig.update_xaxes(tickvals=data["heatmap_x"])
xlen = len(data["heatmap_x"])
fig.update_xaxes(range=[-0.5,xlen-0.5])

xmin = data["heatmap_x"][0]
xmax = data["heatmap_x"][-1]
ymin = data["heatmap_y"][0]
ymax = data["heatmap_y"][-1]

app.layout = dbc.Container([
    html.Div([
        dbc.Row(
            dbc.Col(
                dcc.Graph(
                    id="foo",
                    figure=fig
                ),
            )
        )
    ]),
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
