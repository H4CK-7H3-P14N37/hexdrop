#!/usr/bin/env python3
import os
import re
import datetime
import requests
import pandas as pd
from time import sleep
from api_classes.mail_api import MailAPI

# Define global vars
URL = "https://api.ransomware.live/v2/recentvictims"
DEFAULT_EMAIL = os.getenv('DAILY_DEFAULT_EMAIL')
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
BCC_LIST = os.environ.get('BCC_LIST', [])
if BCC_LIST:
    BCC_LIST = BCC_LIST.split(';')
if isinstance(BCC_LIST, str):
    BCC_LIST = []
REPORT_DIR = os.path.abspath("./reports")

# Make the GET request
headers = {"Accept": "application/json"}
response_data = {}
try:
    response_ok = False
    response = requests.get(URL, headers=headers, timeout=30)
    if not response.ok:
        response_ok = True
    while response_ok:
        print(f"Got Response Code: {response.status_code}... Waiting...")
        sleep(10)
        response = requests.get(URL, headers=headers, timeout=30)
        if response.ok:
            response_data = response.json()
            response_ok = False
except Exception as e:
    print(e)

# Todays date to filter
today_minus_n = datetime.datetime.now()-datetime.timedelta(days=1)

# function to escape domain
def escape_domain(match):
    # Extract the parts of the URL
    scheme = match.group('scheme') or ''
    domain = match.group('domain')
    rest = match.group('rest') or ''
    # Update the scheme: change 'http' to 'hxxp'
    if scheme:
        scheme = scheme.replace('http', 'hxxp', 1)
    # Replace periods in the domain with [.] only
    escaped_domain = domain.replace('.', '[.]')
    return scheme + escaped_domain + rest

pattern = re.compile(
    r'(?P<scheme>https?://)?(?P<domain>(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})(?P<rest>/[^\s]*)?'
)

try:
    # Check if the request was successful
    if response_data:
        data = response_data  # Parse JSON response 
        # Filter data: select only entries where `discovered` starts with today
        filtered_data = []
        for item in data:
            discovered_date = item.get("discovered", "")
            if discovered_date:
                if datetime.datetime.strptime(discovered_date, "%Y-%m-%d %H:%M:%S.%f") >= today_minus_n:
                    filtered_data.append(item)
        
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

        # Formating descriptions and escaping URLs
        email_results = []
        for item in result:
            victim_name = ""
            if item.get("victim"):
                victim_name = pattern.sub(escape_domain, item.get("victim"))
            screenshot_url = ""
            if item.get("screenshot"):
                screenshot_url = item.get("screenshot")
            description = ""
            if item.get("description"):
                description = pattern.sub(escape_domain, item.get("description").replace("\n","<br>"))
            claim_url = ""
            if item.get("claim_url"):
                claim_url = pattern.sub(escape_domain, item.get("claim_url"))
            email_results.append({
                "victim": victim_name,
                # "discovered": item.get("discovered"),
                "screenshot": screenshot_url,
                "description": description,
                "claim_url": claim_url,
            })
        
        # Email results
        mail_obj = MailAPI(EMAIL_USERNAME, EMAIL_PASSWORD)
        # html_body build as we loop
        html_body_list = []
        for r in email_results:
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
        email_body = "<br><br>".join(html_body_list)
        dt_str = datetime.datetime.now().strftime('%Y-%m-%d')
        if not os.path.exists(REPORT_DIR):
            os.mkdir(REPORT_DIR)
        with open(os.path.join(REPORT_DIR,f"{dt_str}.md"), "w") as f:
            f.write(email_body)
        email_subject = f"Hexdrop: {dt_str}"
        send_status = mail_obj.send_mail(
            email_subject,
            email_body,
            EMAIL_USERNAME,
            [DEFAULT_EMAIL], 
            [],
            BCC_LIST,
            inline_files=None,
            attachments=None
        )
except Exception as e:
    print(f"Error: {e}")
