import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

import psycopg2
import numpy as np
import pandas as pd

conn = psycopg2.connect(host="localhost", port = 5432, database="TB")
df_summ = pd.read_sql_query("SELECT vendor, area, sum(price) FROM lvl_bid group by vendor, area", conn)
df_unit = pd.read_sql_query("SELECT vendor, sp_type, area, sum(price) FROM lvl_bid group by vendor, sp_type, area", conn)


units = df_unit.sp_type.unique()
units = np.hstack([units, ['All Units']])
units.sort()

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(
        id="dropdown",
        options=[{"label": x, "value": x} for x in units],
        value=units[0],
        clearable=False,
    ),
    dcc.Graph(id="bar-chart"),
])


@app.callback(
    Output("bar-chart", "figure"), 
    [Input("dropdown", "value")])
def update_bar_chart(unit):

    if unit == units[0]:
        fig = px.bar(df_summ, x="vendor", y="sum", color="area", barmode="group")
    else:
        mask = df_unit["sp_type"] == unit
        fig = px.bar(df_unit[mask], x="vendor", y="sum", color="area", barmode="group")

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
