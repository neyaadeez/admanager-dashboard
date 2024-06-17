from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
import pandas as pd
import os

def initialize_analyticsreporting():
    client_secrets_path = os.path.join(os.path.dirname(__file__), 'client_secret.json')
    
    credentials = service_account.Credentials.from_service_account_file(
        client_secrets_path
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    return client

def get_report(client):
    request = RunReportRequest(
        property='properties/401993563',  # Replace with your actual GA4 property ID
        date_ranges=[{'start_date': '30daysAgo', 'end_date': 'today'}],
        dimensions=[{'name': 'date'}],
        metrics=[
            {'name': 'newUsers'},
            {'name': 'activeUsers'},  # Replace with the correct metric name for Returning Users if different
            {'name': 'eventCount'},  # Assuming 'Key events' refers to event count
            {'name': 'totalUsers'},  # Assuming 'Users' refers to total users
            {'name': 'sessions'}  # Include sessions
        ]
    )
    response = client.run_report(request)
    return response

def print_response(response):
    dimension_headers = [header.name for header in response.dimension_headers]
    metric_headers = [header.name for header in response.metric_headers]

    data = []
    for row in response.rows:
        row_data = {}
        for header, dimension_value in zip(dimension_headers, row.dimension_values):
            row_data[header] = dimension_value.value
        for header, metric_value in zip(metric_headers, row.metric_values):
            row_data[header] = metric_value.value
        data.append(row_data)

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
     
    return df

def fetch_google_analytics_data():
    client = initialize_analyticsreporting()
    response = get_report(client)
    df = print_response(response)
    return df
