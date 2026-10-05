import os
import sys
import json
import time
import logging
from datetime import datetime
import requests
import gspread
from google.oauth2.service_account import Credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1raeLow4QC8RxnWu2EZlY7iPBeXaRI6XlLg28kGygLQA")
SHEET_NAME = os.getenv("SHEET_NAME", "Live_Feed_Stream")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))

SEEN_SLUGS = set()
MAX_CACHE_SIZE = 5000

def get_google_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        creds_info = json.loads(sa_json)
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    elif os.path.exists("service_account.json"):
        creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
    else:
        raise RuntimeError("No Google credentials found! Set GOOGLE_SERVICE_ACCOUNT_JSON env var.")
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

def push_to_sheet(sheet, item):
    slug = item.get("slug", "").strip()
    if slug and slug in SEEN_SLUGS:
        return False
    row = [
        item.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        item.get("agency", "WIRE"),
        item.get("priority", "ROUTINE"),
        slug,
        item.get("headline", ""),
        item.get("raw_byte", ""),
        item.get("speaker", ""),
        item.get("media_link", ""),
        item.get("status_notes", "")
    ]
    sheet.append_row(row)
    if slug:
        SEEN_SLUGS.add(slug)
        if len(SEEN_SLUGS) > MAX_CACHE_SIZE:
            SEEN_SLUGS.pop()
    logging.info(f"[{item.get('agency')}] Ingested {slug}: {item.get('headline')[:45]}...")
    return True

def poll_ani_feed(sheet):
    api_key = os.getenv("ANI_API_KEY")
    user = os.getenv("ANI_USER")
    password = os.getenv("ANI_PASSWORD")
    if not (api_key or (user and password)):
        return
    # Add authenticated ANI API / FTP polling logic here

def poll_pti_feed(sheet):
    user = os.getenv("PTI_USER")
    password = os.getenv("PTI_PASSWORD")
    api_token = os.getenv("PTI_API_TOKEN")
    if not (api_token or (user and password)):
        return
    # Add authenticated PTI NewsML / API polling logic here

def poll_ap_media(sheet):
    api_key = os.getenv("AP_API_KEY")
    if not api_key:
        return
    # Add authenticated AP Media API polling logic here

def poll_ians_feed(sheet):
    user = os.getenv("IANS_USER")
    password = os.getenv("IANS_PASSWORD")
    if not (user and password):
        return
    # Add authenticated IANS polling logic here

def main():
    logging.info("Starting Multi-Agency Wire Cloud Worker...")
    sheet = get_google_sheet()
    while True:
        try:
            poll_ani_feed(sheet)
            poll_pti_feed(sheet)
            poll_ap_media(sheet)
            poll_ians_feed(sheet)
        except Exception as e:
            logging.error(f"Error during poll cycle: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

