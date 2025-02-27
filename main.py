#!/usr/bin/env python3
import os
import datetime
import requests
import pandas as pd
from api_classes.mail_api import MailAPI

# Define global vars
URL = "https://api.ransomware.live/v2/recentvictims"
DEFAULT_EMAIL = os.getenv('DAILY_DEFAULT_EMAIL')
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')


# Make the GET request
headers = {"Accept": "application/json"}
response = requests.get(URL, headers=headers)

# Todays date to filter
today = datetime.datetime.now().strftime("%Y-%m-%d")

# Check if the request was successful
if response.status_code == 200:
    data = response.json()  # Parse JSON response
    
    # Filter data: select only entries where `discovered` starts with today
    filtered_data = [
        item for item in data if item.get("discovered", "").startswith(today)
    ]
    
    # Extract only the required fields
    result = [
        {
            "victim": item.get("victim"),
            # "discovered": item.get("discovered"),
            "screenshot": item.get("screenshot"),
            "description": item.get("description"),
            "claim_url": item.get("claim_url"),
            
        }
        for item in filtered_data
    ]
    
    # Email results
    mail_obj = MailAPI(EMAIL_USERNAME, EMAIL_PASSWORD)
    # html_body build as we loop
    html_body_list = []
    for r in result:
        results_df = pd.DataFrame.from_dict([r])
        # Convert screenshot URLs to img HTML tags
        if not results_df.empty:
            results_df['screenshot'] = results_df['screenshot'].apply(
                lambda x: f'<img src="{x}" width="200">' if pd.notna(x) else ''
            )
        # Transpose DataFrame to display columns vertically
        transposed_df = results_df.T
        # Reset index to make first column a header (removes '0' row)
        transposed_df.columns = ['Details']  # Set a meaningful column name
        results_html = transposed_df.to_html(index=False, classes='stocktable', table_id='table1', escape=False)
        results_html = results_html.replace(
            'class="dataframe ',
            'class="'
        ).replace(
            '<tr style="text-align: right;">',
            '<tr style="text-align: left;">'
        )
        html_body_list.append(results_html)
    send_status = mail_obj.send_mail(
        f"Daily Hexdrop Summary",
        f"{'<br><br>'.join(html_body_list)}<br>",
        EMAIL_USERNAME,
        [DEFAULT_EMAIL], 
        [],
        [],
        inline_files=None,
        attachments=None
    )
else:
    print(f"Error: {response.status_code}, {response.text}")
