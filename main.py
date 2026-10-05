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
logger = logging.getLogger(__name__)

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1raeLow4QC8RxnWu2EZlY7iPBeXaRI6XlLg28kGygLQA")
SHEET_NAME = os.getenv("SHEET_NAME", "Live_Feed_Stream")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))

SEEN_SLUGS = set()
MAX_CACHE_SIZE = 5000

def get_google_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        sa_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if sa_json:
            creds_info = json.loads(sa_json)
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
            logger.info("✓ Google credentials loaded from env var")
        elif os.path.exists("service_account.json"):
            creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
            logger.info("✓ Google credentials loaded from file")
        else:
            logger.error("✗ No Google credentials found!")
            raise RuntimeError("No Google credentials found! Set GOOGLE_SERVICE_ACCOUNT_JSON env var.")
        
        client = gspread.authorize(creds)
        logger.info(f"✓ Authorized with Google Sheets API")
        
        logger.info(f"Opening spreadsheet ID: {SPREADSHEET_ID}")
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        logger.info(f"✓ Spreadsheet opened: {spreadsheet.title}")
        
        logger.info(f"Looking for sheet: '{SHEET_NAME}'")
        sheet = spreadsheet.worksheet(SHEET_NAME)
        logger.info(f"✓ Sheet found: '{SHEET_NAME}'")
        return sheet
    except Exception as e:
        logger.error(f"✗ Error connecting to Google Sheet: {type(e).__name__}: {e}")
        raise

def push_to_sheet(sheet, item):
    try:
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
        logger.info(f"[{item.get('agency')}] Ingested {slug}: {item.get('headline')[:45]}...")
        return True
    except Exception as e:
        logger.error(f"✗ Error pushing row to sheet: {type(e).__name__}: {e}")
        return False

def poll_ani_feed(sheet):
    api_key = os.getenv("ANI_API_KEY")
    user = os.getenv("ANI_USER")
    password = os.getenv("ANI_PASSWORD")
    if not (api_key or (user and password)):
        logger.debug("ANI credentials not configured")
        return
    logger.debug("Polling ANI feed...")
    # Add authenticated ANI API / FTP polling logic here

def poll_pti_feed(sheet):
    user = os.getenv("PTI_USER")
    password = os.getenv("PTI_PASSWORD")
    api_token = os.getenv("PTI_API_TOKEN")
    if not (api_token or (user and password)):
        logger.debug("PTI credentials not configured")
        return
    logger.debug("Polling PTI feed...")
    # Add authenticated PTI NewsML / API polling logic here

def poll_ap_media(sheet):
    api_key = os.getenv("AP_API_KEY")
    if not api_key:
        logger.debug("AP Media credentials not configured")
        return
    logger.debug("Polling AP Media feed...")
    # Add authenticated AP Media API polling logic here

def poll_ians_feed(sheet):
    user = os.getenv("IANS_USER")
    password = os.getenv("IANS_PASSWORD")
    if not (user and password):
        logger.debug("IANS credentials not configured")
        return
    logger.debug("Polling IANS feed...")
    # Add authenticated IANS polling logic here

def main():
    logger.info("=" * 60)
    logger.info("Starting Multi-Agency Wire Cloud Worker...")
    logger.info(f"Spreadsheet ID: {SPREADSHEET_ID}")
    logger.info(f"Sheet Name: {SHEET_NAME}")
    logger.info(f"Poll Interval: {POLL_INTERVAL}s")
    logger.info("=" * 60)
    
    try:
        sheet = get_google_sheet()
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheet. Exiting.")
        sys.exit(1)
    
    logger.info("✓ Worker initialized successfully. Starting poll loop...")
    
    poll_count = 0
    while True:
        try:
            poll_count += 1
            logger.info(f"[Poll #{poll_count}] Starting feed poll cycle...")
            poll_ani_feed(sheet)
            poll_pti_feed(sheet)
            poll_ap_media(sheet)
            poll_ians_feed(sheet)
            logger.info(f"[Poll #{poll_count}] Feed poll cycle complete. Next in {POLL_INTERVAL}s")
        except Exception as e:
            logger.error(f"Error during poll cycle #{poll_count}: {type(e).__name__}: {e}")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

