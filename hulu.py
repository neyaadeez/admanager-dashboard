import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Hulu Campaign Data Visualization"),
    dcc.Input(id='campaign-url', type='text', placeholder='Enter Hulu campaign URL', style={'width': '50%'}),
    html.Button('Submit', id='submit-button', n_clicks=0),
    dcc.Loading(id='loading', children=[
        dcc.Graph(id='campaign-graph')
    ], type='default')
])

def extract_table_data(table):
    headers = table.find_elements(By.TAG_NAME, 'th')
    headers = [header.text for header in headers]

    rows = table.find_elements(By.TAG_NAME, 'tr')
    data = []
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, 'td')
        cols = [col.text for col in cols]
        if cols:
            data.append(cols)

    if headers and data:
        return pd.DataFrame(data, columns=headers)
    else:
        return pd.DataFrame()

def extract_category_names(categories):
    return [category.split('|')[-1].strip() for category in categories]

def scrape_campaign_data(campaign_url):
    driver = webdriver.Chrome()
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=('Total Impressions Over Time', 'Impressions by Audiences', 'Impressions by Platforms', 'Impressions by Content Genres'),
                        vertical_spacing=0.3, horizontal_spacing=0.2)
    try:
        driver.get('https://admanager.hulu.com/login')

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'email')))
        username = driver.find_element(By.NAME, 'email')
        password = driver.find_element(By.NAME, 'password')

        username.send_keys(os.getenv('USERNAME'))
        password.send_keys(os.getenv('PASSWORD'))
        password.send_keys(Keys.RETURN)

        time.sleep(5)

        driver.get(campaign_url)

        time.sleep(5)

        tables = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'table'))
        )

        for i, (row, col) in zip([0, 3, 4, 5], [(1, 1), (1, 2), (2, 1), (2, 2)]):
            if len(tables) > i:
                df = extract_table_data(tables[i])
                if not df.empty:
                    if i == 0 and 'Total Impressions' in df.columns:
                        df['Total Impressions'] = df['Total Impressions'].str.replace(' impressions', '').str.replace(',', '').astype(int)
                        if 'Days' in df.columns:
                            df['Start Date'] = df['Days'].str.split(' - ').str[0]
                            df['Start Date'] = pd.to_datetime(df['Start Date'], format='%a, %m/%d/%y')
                            fig.add_trace(go.Scatter(x=df['Start Date'], y=df['Total Impressions'], mode='lines+markers', name='Total Impressions'), row=row, col=col)

                    if i == 3:
                        df['Audiences'] = extract_category_names(df['Audiences'])
                        df['Impressions'] = df['Impressions'].str.replace(' impressions', '').str.replace(',', '').astype(int)
                        fig.add_trace(go.Bar(x=df['Impressions'], y=df['Audiences'], orientation='h', name='Impressions by Audiences'), row=row, col=col)

                    if i == 4:
                        df['Impressions'] = df['Impressions'].str.replace(' impressions', '').str.replace(',', '').astype(int)
                        fig.add_trace(go.Bar(x=df['Platforms'], y=df['Impressions'], name='Impressions by Platforms'), row=row, col=col)

                    if i == 5:
                        df['Impressions'] = df['Impressions'].apply(lambda x: int(x.replace(' impressions', '').replace(',', '')) if x.replace(' impressions', '').replace(',', '').isdigit() else 0)
                        fig.add_trace(go.Bar(x=df['Content Genres'], y=df['Impressions'], name='Impressions by Content Genres'), row=row, col=col)

        fig.update_layout(height=1050, width=1680, title_text="Hulu Campaign Data Visualization")
        
        # Return the figure object
        return fig
    
    finally:
        driver.quit()

def save_html(html_content, file_path):
    with open(file_path, 'w') as f:
        f.write(html_content)

@app.callback(
    Output('campaign-graph', 'figure'),
    [Input('submit-button', 'n_clicks')],
    [State('campaign-url', 'value')]
)
def update_graph(n_clicks, campaign_url):
    if n_clicks > 0 and campaign_url:
        fig = scrape_campaign_data(campaign_url)
        fig_html = fig.to_html()
        save_html(fig_html, 'output.html')
        return fig
    return {}

if __name__ == '__main__':
    app.run_server(debug=True)