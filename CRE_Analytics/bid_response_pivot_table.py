import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_pivottable
import pandas as pd
import sys
import os
import numpy as np
import shortuuid
import sys

filein = "tailorbird/d_analytics/data/processed/" + "Cost Comparison_DATA Kings Colony v2.csv"
df = pd.read_csv(filein, header=None)
data = df.values.tolist()

file_l = os.listdir("tailorbird/d_analytics/data/processed/")
file_l = np.hstack([file_l, ['At your choice (Choose a project)']])
file_l.sort()

app = dash.Dash(__name__)
app.title = 'Tailorbird Bid Response Analyzer'

cols = ['GC']
rows = ['Category']

t_id = shortuuid.uuid()

app.layout = html.Div([


    dcc.Dropdown(
        id="dropdown",
        options=[{"label": x, "value": x} for x in file_l],
        value=file_l[0],
        clearable=False,
    ),

    html.Div(id=t_id)
])

@app.callback(Output(t_id, "children"),
              [Input("dropdown", "value")])
def refresh_pivottable(project):

    print(project)

    if project == file_l[0]:
        filein = "tailorbird/d_analytics/data/processed/" + "Cost Comparison_DATA Kings Colony v2.csv"
    else:
        filein = "tailorbird/d_analytics/data/processed/" + project

    df = pd.read_csv(filein, header=None)
    print(df.shape)
    data = df.values.tolist()

    return([


        dash_pivottable.PivotTable(
        id='table',
        data=data,
        cols=cols,
        colOrder="key_a_to_z",
        rows=rows,
        rowOrder="key_a_to_z",
        rendererName="Table",
        aggregatorName="Sum",
        vals=["Avg_Price_Per_Unit", "Quantity"],
        hiddenAttributes=['Scope',
                    'Total_Units',
                    'Response_Flag',
                    'idx'],
        unusedOrientationCutoff=250
        ),
        html.Div(id=shortuuid.uuid())
        ])


if __name__ == '__main__':
    
    app.run_server(debug=True, port=sys.argv[1])
