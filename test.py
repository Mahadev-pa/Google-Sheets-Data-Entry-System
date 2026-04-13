"""
TEST SCRIPT - Google Sheets Connection Test
हे चालवून बघ की सगळं सेट आहे का
"""

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive']

def test_connection():
    print("🔐 Connecting to Google Sheets...")
    
    creds = None
    
    # Check if we have saved token
    if os.path.exists('token.json'):
        print("📁 Found existing token.json")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, ask user to login
    if not creds or not creds.valid:
        print("🔄 Need authentication. Opening browser...")
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("✅ Token refreshed")
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ Authentication successful")
        
        # Save credentials for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("💾 Token saved to token.json")
    
    # Authorize gspread
    client = gspread.authorize(creds)
    print("✅ Connected to Google Sheets API")
    
    # IMPORTANT: Change this to YOUR sheet name
    SHEET_NAME = "MyData"  # 🔴 येथे तुमच्या Sheet चं नाव लिहा
    
    try:
        # Open spreadsheet
        spreadsheet = client.open(SHEET_NAME)
        print(f"✅ Opened spreadsheet: {SHEET_NAME}")
        
        # Get first sheet
        worksheet = spreadsheet.sheet1
        print(f"✅ Opened worksheet: {worksheet.title}")
        
        # Test write
        test_value = f"✅ Connection Test - {__import__('datetime').datetime.now()}"
        worksheet.update_cell(1, 1, test_value)
        print(f"✅ Wrote test data to cell A1: {test_value}")
        
        print("\n" + "="*50)
        print("🎉 SUCCESS! Everything is working!")
        print("="*50)
        print(f"👉 Check your Google Sheet '{SHEET_NAME}' - Cell A1 should be updated")
        
        return True
        
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"\n❌ ERROR: Spreadsheet '{SHEET_NAME}' not found!")
        print("📝 Solutions:")
        print("   1. Make sure you created the sheet in Google Drive")
        print("   2. Check the spelling (case sensitive)")
        print("   3. Update SHEET_NAME variable with correct name")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("GOOGLE SHEETS CONNECTION TEST")
    print("="*50)
    test_connection()   