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

def getData(filename):
    filein = "tailorbird/d_analytics/data/processed/" + filename
    df = pd.read_csv(filein, header=None)
    return(df.values.tolist())

file_l = os.listdir("tailorbird/d_analytics/data/processed/")
file_l = [x for x in file_l if not x.startswith('.')]
##file_l = np.hstack([file_l, ['At your choice (Choose a project)']])
file_l.sort()

app = dash.Dash(__name__)
app.title = 'Tailorbird Bid Response Analyzer'

cols = ['GC']
rows = ['Category']

project = "Cost Comparison_Kings Colony.csv"

data = getData(project)

app.layout = html.Div([

    dcc.Dropdown(
        id="dropdown",
        options=[{"label": x, "value": x} for x in file_l],
        value=file_l[0],
        clearable=False,
        placeholder="Select a project",
    ),

    

    html.Div(id='output')
])

@app.callback(Output('output', 'children'),
              [Input("dropdown", "value")])
def display_props(project):
    print(project)

    #if project == file_l[0]:
    #    project = "Cost Comparison_Kings Colony.csv"

    data = getData(project)

    return(dash_pivottable.PivotTable(
        id=shortuuid.uuid(),
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
        unusedOrientationCutoff=80)
    )

if __name__ == '__main__':
    
    app.run_server(debug=True, port=4000)
