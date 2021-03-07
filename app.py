"""TODO..."""

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

from data_parser import get_data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

data = get_data()

heatmap_object = go.Heatmap(
    z=data["heatmap_z"],
    x=data["heatmap_x"],
    y=data["heatmap_y"],
    colorscale="Greys",
    hoverlabel={"font_size": 18},
    hoverinfo="text",
    text=data["heatmap_cell_text"],
    xgap=10,
    showscale=False
)

fig = go.Figure(heatmap_object)
fig.update_xaxes(type="category")
fig.update_yaxes(visible=False)
fig.update_layout(font={"size": 18})
fig.update_layout(width=len(data["heatmap_x"])*25, autosize=False)
fig.update_layout(plot_bgcolor="white")
fig.update_layout(margin={"l": 0, "r": 0})

insertions_trace = go.Scatter(
    x=data["insertions_x"],
    y=data["insertions_y"],
    hoverinfo="skip",
    mode="markers",
    marker={
        "color": "lime",
        "size": 18,
        "symbol": "cross"
    },
    showlegend=False
)
deletions_trace = go.Scatter(
    x=data["deletions_x"],
    y=data["deletions_y"],
    hoverinfo="skip",
    mode="markers",
    marker={
        "color": "red",
        "size": 18,
        "symbol": "x"
    },
    showlegend=False
)
fig.add_trace(insertions_trace)
fig.add_trace(deletions_trace)

heatmap_y_axis_object = go.Heatmap(
    z=[[0], [0], [0]],
    x=[1],
    y=data["heatmap_y"],
    showscale=False,
    hoverinfo="none",
    colorscale="Greys",
    zmin=0,
    zmax=1
)
left_fig = go.Figure(heatmap_y_axis_object)
left_fig.update_layout(font={"size": 18})
left_fig.update_layout(margin={"l": 0, "r": 0})
left_fig.update_layout(plot_bgcolor="white")
left_fig.update_xaxes(visible=False)
left_fig.update_yaxes(visible=False)

y_axis_trace = go.Scatter(
    y=data["heatmap_y"],
    x=[0, 0, 0],
    hoverinfo="skip",
    mode="markers+text",
    marker={
        "color": "white",
        "size": 1
    },
    text=data["heatmap_y"],
    textposition="middle center"
)
left_fig.add_trace(y_axis_trace)

heatmap_colorbar_object = go.Heatmap(
    z=[[0], [0], [0]],
    x=["foo"],
    y=data["heatmap_y"],
    colorscale="Greys"
)
right_fig = go.Figure(heatmap_colorbar_object)
right_fig_trace_selector = {"type": "heatmap"}
right_fig.update_traces(zmin=0, selector=right_fig_trace_selector)
right_fig.update_traces(zmax=1, selector=right_fig_trace_selector)
right_fig.update_traces(xgap=0, selector=right_fig_trace_selector)
right_fig.update_traces(hoverinfo="skip", selector=right_fig_trace_selector)
right_fig.update_xaxes(visible=False)
right_fig.update_yaxes(visible=False)

row = html.Div(
    [
        dbc.Row(dbc.Col(html.Div("A single column"))),
        dbc.Row(
            [
                dbc.Col(html.Div("One of three columns")),
                dbc.Col(html.Div("One of three columns")),
                dbc.Col(html.Div("One of three columns")),
            ]
        ),
    ]
)

heatmap_row = html.Div([
    dbc.Row([
        dbc.Col(
            html.Div(
                dcc.Graph(id="heatmap-axis", figure=left_fig),
                style={"width": "90vw", "overflowX": "hidden"}
            ),
            width=1
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(id="heatmap", figure=fig),
                style={"overflowX": "scroll"}
            ),
            width=10
        ),
        dbc.Col(
            html.Div(
                dcc.Graph(id="heatmap-color-bar", figure=right_fig),
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
     inputs=[Input('heatmap', 'clickData')])
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
