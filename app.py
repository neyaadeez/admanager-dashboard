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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

# Adding external stylesheet for custom styling
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css']
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
        dcc.Loading(id="loading-icon", children=[
            html.Div(id='form-or-graph', children=[
                html.Div(id='form-container', children=[
                    html.H2('Enter your Hulu Credentials and Campaign URL', className='mb-4'),
                    html.Div(className="form-group", children=[
                        html.Label("Email:", htmlFor="email"),
                        dcc.Input(id='email', type='email', placeholder='Enter your email', className='form-control', required=True)
                    ]),
                    html.Div(className="form-group", children=[
                        html.Label("Password:", htmlFor="password"),
                        dcc.Input(id='password', type='password', placeholder='Enter your password', className='form-control', required=True)
                    ]),
                    html.Div(className="form-group", children=[
                        html.Label("Campaign URL:", htmlFor="campaign-url"),
                        dcc.Input(id='campaign-url', type='text', placeholder='Enter Hulu campaign URL', className='form-control', required=True)
                    ]),
                    html.Button('Submit', id='submit-button', n_clicks=0, className='btn btn-primary btn-block'),
                ])
            ])
        ], type='default')
    ])
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

def scrape_campaign_data(email, password, campaign_url):
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')  # Run Firefox in headless mode
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Firefox(options=options)
    graphs = []
    try:
        driver.get('https://admanager.hulu.com/login')

        try:
            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.NAME, 'email')))
        except TimeoutException:
            return "Error: Login page took too long to load."
        
        username = driver.find_element(By.NAME, 'email')
        pwd = driver.find_element(By.NAME, 'password')

        username.send_keys(email)
        pwd.send_keys(password)
        pwd.send_keys(Keys.RETURN)

        time.sleep(5)

        driver.get(campaign_url)

        time.sleep(5)

        try:
            tables = WebDriverWait(driver, 100).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'table'))
            )
        except TimeoutException:
            return "Error: Campaign data page took too long to load."

        fig = make_subplots(rows=4, cols=1, 
                            subplot_titles=('Total Impressions Over Time', 'Impressions by Audiences', 'Impressions by Platforms', 'Impressions by Content Genres'),
                            vertical_spacing=0.1)

        if len(tables) > 0:
            df = extract_table_data(tables[0])
            if not df.empty:
                df['Total Impressions'] = df['Total Impressions'].str.replace(' impressions', '').str.replace(',', '').astype(int)
                if 'Days' in df.columns:
                    df['Start Date'] = df['Days'].str.split(' - ').str[0]
                    df['Start Date'] = pd.to_datetime(df['Start Date'], format='%a, %m/%d/%y')
                    fig.add_trace(go.Scatter(x=df['Start Date'], y=df['Total Impressions'], mode='lines+markers', name='Total Impressions'), row=1, col=1)
                    fig.update_yaxes(title_text='Total Impressions', row=1, col=1)

        if len(tables) > 3:
            df = extract_table_data(tables[3])
            if not df.empty:
                df['Audiences'] = extract_category_names(df['Audiences'])
                df['Impressions'] = df['Impressions'].str.replace(' impressions', '').str.replace(',', '').astype(int)
                fig.add_trace(go.Bar(x=df['Impressions'], y=df['Audiences'], orientation='h', name='Impressions by Audiences'), row=2, col=1)
                fig.update_yaxes(title_text='Audiences', row=2, col=1)

        if len(tables) > 4:
            df = extract_table_data(tables[4])
            if not df.empty:
                df['Impressions'] = df['Impressions'].str.replace(' impressions', '').str.replace(',', '').astype(int)
                fig.add_trace(go.Bar(x=df['Platforms'], y=df['Impressions'], name='Impressions by Platforms'), row=3, col=1)
                fig.update_yaxes(title_text='Impressions', row=3, col=1)

        if len(tables) > 5:
            df = extract_table_data(tables[5])
            if not df.empty:
                df['Impressions'] = df['Impressions'].apply(lambda x: int(x.replace(' impressions', '').replace(',', '')) if x.replace(' impressions', '').replace(',', '').isdigit() else 0)
                fig.add_trace(go.Bar(x=df['Content Genres'], y=df['Impressions'], name='Impressions by Content Genres'), row=4, col=1)
                fig.update_yaxes(title_text='Impressions', row=4, col=1)

        fig.update_layout(height=1500, width=1200, title_text="Hulu Campaign Data Visualization")
        graphs.append(dcc.Graph(figure=fig))

    except NoSuchElementException as e:
        return f"Error: Unable to locate an element. Details: {e}"
    except Exception as e:
        return f"An error occurred: {e}"
    finally:
        driver.quit()
    return graphs

@app.callback(
    Output('form-or-graph', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('email', 'value'), State('password', 'value'), State('campaign-url', 'value')]
)
def update_graph(n_clicks, email, password, campaign_url):
    if n_clicks > 0 and email and password and campaign_url:
        graphs = scrape_campaign_data(email, password, campaign_url)
        return graphs
    return html.Div(id='form-container', children=[
        html.H2('Enter your Hulu Credentials and Campaign URL', className='mb-4'),
        html.Div(className="form-group", children=[
            html.Label("Email:", htmlFor="email"),
            dcc.Input(id='email', type='email', placeholder='Enter your email', className='form-control', required=True)
        ]),
        html.Div(className="form-group", children=[
            html.Label("Password:", htmlFor="password"),
            dcc.Input(id='password', type='password', placeholder='Enter your password', className='form-control', required=True)
        ]),
        html.Div(className="form-group", children=[
            html.Label("Campaign URL:", htmlFor="campaign-url"),
            dcc.Input(id='campaign-url', type='text', placeholder='Enter Hulu campaign URL', className='form-control', required=True)
        ]),
        html.Button('Submit', id='submit-button', n_clicks=0, className='btn btn-primary btn-block'),
    ], style={'max-width': '500px', 'margin': '0 auto', 'padding-top': '50px'})


if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port="8050")
