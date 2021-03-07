import csv
import os

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

x = []
y = []
mutations = {}
insertions_x = []
insertions_y = []
deletions_x = []
deletions_y = []

# TODO: Input data standards will be crucial moving forward.
with os.scandir("data") as it:
    for entry in it:
        strain = entry.name.split("_")[0]
        y += [strain]
        mutations[strain] = {}
        with open(entry.path) as fp:
            reader = csv.DictReader(fp, delimiter="\t")
            for row in reader:
                pos = int(row["POS"])
                alt = row["ALT"]
                x += [pos]
                mutations[strain][pos] = {
                    "alt_freq": float(row["ALT_FREQ"]),
                    "ref": row["REF"],
                    "alt": row["ALT"],
                }
                if alt[0] == "+":
                    insertions_x += [pos]
                    insertions_y += [strain]
                elif alt[0] == "-":
                    deletions_x += [pos]
                    deletions_y += [strain]

x = list(set(x))
x.sort()

z = []
text = []
for strain in y:
    inner_z = []
    inner_text = []
    for pos in x:
        if pos in mutations[strain]:
            vals = mutations[strain][pos]
            inner_z += [vals["alt_freq"]]
            inner_text += ["Pos %s; %s to %s; Freq %s"
                           % (pos, vals["ref"], vals["alt"], vals["alt_freq"])]
        else:
            inner_z += [0]
            inner_text += [None]
    z += [inner_z]
    text += [inner_text]

heatmap_object = go.Heatmap(
    z=z,
    x=x,
    y=y,
    colorscale="Greys",
    hoverlabel={"font_size": 18},
    hoverinfo="text",
    text=text,
    xgap=10,
    showscale=False
)

fig = go.Figure(heatmap_object)
fig.update_xaxes(type="category")
fig.update_yaxes(visible=False)
fig.update_layout(font={"size": 18})
fig.update_layout(width=len(x)*25, autosize=False)
fig.update_layout(plot_bgcolor="white")
fig.update_layout(margin={"l": 0, "r": 0})

insertions_trace = go.Scatter(
    x=insertions_x,
    y=insertions_y,
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
    x=deletions_x,
    y=deletions_y,
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
    y=y,
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
    y=y,
    # x=["foo", "foo", "foo"],
    x=[0, 0, 0],
    hoverinfo="skip",
    mode="markers+text",
    marker={
        "color": "white",
        "size": 1
    },
    text=y,
    textposition="middle center"
)
left_fig.add_trace(y_axis_trace)

heatmap_colorbar_object = go.Heatmap(
    z=[[0], [0], [0]],
    x=["foo"],
    y=y,
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
    cell_vals = []

    if clickData is None:
        table_strain = y[0]
    else:
        table_strain = clickData["points"][0]["y"]

    table_strain_data = mutations[table_strain]
    cell_vals += [list(table_strain_data.keys())]
    for header_val in header_vals[1:]:
        col = []
        for pos in table_strain_data:
            col += [table_strain_data[pos][header_val]]
        cell_vals += [col]

    table_obj = go.Table(
        header={"values": ["<b>%s</b>" % e for e in header_vals],
                "line_color": "black",
                "fill_color": "white",
                "height": 32,
                "font": {"size": 18}
                },
        cells={"values": cell_vals,
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
