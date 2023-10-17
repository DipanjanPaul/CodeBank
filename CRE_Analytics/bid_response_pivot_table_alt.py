import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_pivottable
import pandas as pd

filein = "tailorbird/d_analytics/data/processed/Cost Comparison_Hammocks Place.csv"
df = pd.read_csv(filein, header=None)
data = df.values.tolist()

app = dash.Dash(__name__)
app.title = 'Tailorbird Bid Response Analyzer'

cols = ['GC']
rows = ['Category']

app.layout = html.Div([
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
    html.Div(
        id='output'
    )
])


@app.callback(Output('output', 'children'),
              [Input('table', 'cols'),
               Input('table', 'rows'),
               Input('table', 'rowOrder'),
               Input('table', 'colOrder'),
               Input('table', 'aggregatorName'),
               Input('table', 'rendererName')])
def display_props(cols, rows, row_order, col_order, aggregator, renderer):
    return [
        html.P(str(cols), id='columns'),
        html.P(str(rows), id='rows'),
        html.P(str(row_order), id='row_order'),
        html.P(str(col_order), id='col_order'),
        html.P(str(aggregator), id='aggregator'),
        html.P(str(renderer), id='renderer'),
    ]


if __name__ == '__main__':
    
    app.run_server(debug=True, port=4000)
