import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

st.title("Hulu Campaign Data Visualization")

campaign_url = st.text_input('Enter Hulu campaign URL')

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

        username.send_keys('demi@backbonesociety.com')
        password.send_keys('Drobotya20!')
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

        fig.layout(height=1000, width=1200, title_text="Hulu Campaign Data Visualization")
    finally:
        driver.quit()
    return fig

if st.button('Submit'):
    if campaign_url:
        fig = scrape_campaign_data(campaign_url)
        st.plotly_chart(fig)
