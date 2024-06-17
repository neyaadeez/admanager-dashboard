import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google_analytics import fetch_google_analytics_data
from datetime import datetime, timedelta

external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css', '/assets/styles.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True

app.layout = html.Div(children=[
    html.Nav(className='navbar navbar-expand-lg', children=[
        html.A(className='navbar-brand', href='/', children=[
            html.Img(src='/assets/logo_footer.webp', id='logo')
        ]),
        html.Button(className='navbar-toggler', type='button', **{
            'data-toggle': 'collapse', 'data-target': '#navbarNav', 'aria-controls': 'navbarNav', 'aria-expanded': 'false', 'aria-label': 'Toggle navigation'
        }, children=[
            html.Span(className='navbar-toggler-icon')
        ])
    ]),
    html.Div(className='container mt-4', children=[
        html.Div(id='form-or-dashboard', children=[
            dcc.Loading(id='loading', children=[
                html.Div(id='form-container', style={'textAlign': 'center', 'paddingTop': '20%'}, children=[
                    html.Button('Google Analytics Data Visualization', id='load-data-button', n_clicks=0, className='btn btn-primary')
                ]),
                html.Div(id='graph-container', style={'display': 'none'})
            ], type='default')
        ])
    ])
])

@app.callback(
    [Output('form-container', 'style'),
     Output('graph-container', 'style'),
     Output('graph-container', 'children')],
    [Input('load-data-button', 'n_clicks')]
)
def update_graph(n_clicks):
    if n_clicks > 0:
        df = fetch_google_analytics_data()
        
        # Log the fetched data
        print("Fetched data:")
        print(df.head())
        print("Data summary:")
        print(df.describe())

        if not df.empty:
            # Convert 'date' column to datetime and filter for the last 30 days
            df['date'] = pd.to_datetime(df['date'])
            end_date = df['date'].max()
            start_date = end_date - timedelta(days=30)
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

            # Convert relevant columns to numeric types
            df['newUsers'] = pd.to_numeric(df['newUsers'])
            df['activeUsers'] = pd.to_numeric(df['activeUsers'])
            df['eventCount'] = pd.to_numeric(df['eventCount'])
            df['totalUsers'] = pd.to_numeric(df['totalUsers'])
            df['sessions'] = pd.to_numeric(df['sessions'])

            # Sort the DataFrame by date
            df = df.sort_values(by='date')

            fig = make_subplots(rows=5, cols=1, 
                                subplot_titles=('New Users', 'Returning Users', 'Key Events', 'Users', 'Sessions'),
                                vertical_spacing=0.1)

            # Add individual metrics as separate graphs with y-axis starting from 0
            fig.add_trace(go.Scatter(x=df['date'], y=df['newUsers'], mode='lines+markers', name='New Users'), row=1, col=1)
            fig.update_yaxes(title_text='New Users', row=1, col=1, range=[0, df['newUsers'].max() + 5])

            fig.add_trace(go.Scatter(x=df['date'], y=df['activeUsers'], mode='lines+markers', name='Returning Users'), row=2, col=1)
            fig.update_yaxes(title_text='Returning Users', row=2, col=1, range=[0, df['activeUsers'].max() + 5])

            fig.add_trace(go.Scatter(x=df['date'], y=df['eventCount'], mode='lines+markers', name='Key Events'), row=3, col=1)
            fig.update_yaxes(title_text='Key Events', row=3, col=1, range=[0, df['eventCount'].max() + 5])

            fig.add_trace(go.Scatter(x=df['date'], y=df['totalUsers'], mode='lines+markers', name='Users'), row=4, col=1)
            fig.update_yaxes(title_text='Users', row=4, col=1, range=[0, df['totalUsers'].max() + 5])

            fig.add_trace(go.Scatter(x=df['date'], y=df['sessions'], mode='lines+markers', name='Sessions'), row=5, col=1)
            fig.update_yaxes(title_text='Sessions', row=5, col=1, range=[0, df['sessions'].max() + 5])

            fig.update_layout(height=1500, width=1200, title_text="Google Analytics Data")
            return {'display': 'none'}, {'display': 'block'}, dcc.Graph(figure=fig)
    return {'textAlign': 'center', 'paddingTop': '20%'}, {'display': 'none'}, None

if __name__ == '__main__':
    app.run_server(debug=True)
