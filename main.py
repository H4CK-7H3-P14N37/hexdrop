#!/usr/bin/env python3
import os
import re
import datetime
import requests
from time import sleep
from deadletterbox import Mailer, ReportBuilder

# Define global vars
URL = "https://api-pro.ransomware.live/victims/recent?order=discovered"
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
def get_data():
    headers = {
        "Accept": "application/json",
        "X-API-KEY": os.getenv('API_KEY')
    }
    response_data = {}
    try:
        response_ok = False
        response = requests.get(URL, headers=headers, timeout=30)
        response_data = response.json()
        if not response.ok:
            response_ok = True
        while response_ok:
            print(f"Got Response Code: {response.status_code}... Waiting...")
            sleep(10)
            response = requests.get(URL, headers=headers, timeout=30)
            if response.ok:
                response_data = response.json()
                response_ok = False
        return response_data
    except Exception as e:
        print(e)
        get_data()

response_data = get_data().get('victims', {})

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
                if datetime.datetime.fromisoformat(discovered_date).replace(tzinfo=None) >= today_minus_n:
                    filtered_data.append(item)
        
        # Extract only the required fields
        result = [
            {
                "victim": item.get("victim"),
                # "discovered": item.get("discovered"),
                "screenshot": item.get("screenshot"),
                "description": item.get("description"),
                "claim_url": item.get("post_url"),
                
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
        mail_obj = Mailer(EMAIL_USERNAME, EMAIL_PASSWORD)
        dt_str = datetime.datetime.now().strftime('%Y-%m-%d')
        report = ReportBuilder(
            title="Hexdrop",
            subtitle=f"Ransomware victims discovered {dt_str}",
        )
        for r in email_results:
            victim_name = r.get("victim") or "Unknown victim"
            screenshot_html = f'<img src="{r["screenshot"]}" width="200">' if r.get("screenshot") else "No screenshot available"
            report.add_table(
                {
                    "Victim": {"Details": victim_name},
                    "Screenshot": {"Details": screenshot_html},
                    "Description": {"Details": r.get("description", "No Description")},
                    "Claim URL": {"Details": r.get("claim_url", "No URL")},
                },
                heading=victim_name,
                index_label="Field",
            )
        email_body = report.build_html()
        if not os.path.exists(REPORT_DIR):
            os.mkdir(REPORT_DIR)
        with open(os.path.join(REPORT_DIR,f"{dt_str}.md"), "w") as f:
            f.write(email_body)
        email_subject = f"Hexdrop: {dt_str}"
        send_status = mail_obj.send_simple(
            email_subject,
            EMAIL_USERNAME,
            to=[DEFAULT_EMAIL],
            cc=[],
            bcc=BCC_LIST,
            html=email_body,
            attachments=None,
            inline_images=None
        )
except Exception as e:
    print(f"Error: {e}")
