import json
import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth import default

def get_people_from_sheet(is_test_mode=None):
    """Gets people data directly from a Google Sheet
    
    Args:
        is_test_mode: Boolean indicating if running in test mode
        
    Returns:
        tuple: (people_data, people_by_email, relationship_levels) - Dictionaries with people's details 
               indexed by name and email, and relationship level definitions
    """
    
    # Configure the connection
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SPREADSHEET_ID = '1Hg5d-wXrxdsf9FgtH3h6Bq86w_ipr1akv_E_KbLFdYE'  # From the URL of your sheet
    RANGE_NAME = 'Emails!A2:F500'  # Adjust based on your data layout
    
    # If is_test_mode wasn't passed, check the environment variable
    if is_test_mode is None:
        is_test_mode = os.environ.get('SULLSTICE_TEST_MODE', 'False').lower() == 'true'
    
    try:
        if is_test_mode:
            # In test mode, use the service account file
            logging.info("Sheet access: Running in test mode, using service account file")
            SERVICE_ACCOUNT_FILE = 'sullstice-a60fa1da2edb.json'
            
            # Print the service account email for verification (in test mode only)
            with open(SERVICE_ACCOUNT_FILE, 'r') as f:
                service_account_info = json.load(f)
                service_account_email = service_account_info.get('client_email')
                logging.info(f"Service account email: {service_account_email}")
                logging.info(f"Please make sure this email has viewer access to your spreadsheet")
            
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        else:
            # In production, rely on the service account running the app
            logging.info("Sheet access: Running in production mode, using default credentials")
            credentials, project = default(scopes=SCOPES)
            logging.info(f"Using default GCP credentials for project: {project}")
    except Exception as e:
        logging.error(f"Error with authentication: {e}")
        return {}, {}, {}
    
    # Build the service with the appropriate credentials
    service = build('sheets', 'v4', credentials=credentials)
    
    # Test access to the API
    try:
        metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        logging.info(f"Successfully connected to spreadsheet: {metadata.get('properties', {}).get('title')}")
    except Exception as e:
        logging.error(f"API access error: {str(e)}")
        return {}, {}, {}

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    rows = result.get('values', [])
    
    if not rows:
        logging.info('No data found.')
        return {}, {}, {}
    
    # Define relationship levels
    relationship_levels = {
        "1": "very good close friend i see often",
        "2": "family, very close",
        "3": "very good close friend i don't see very often",
        "4": "good friend mostly connected through my softabll team",
        "5": "friend through sullstice - mostly just see them there",
        "6": "good friend but we haven't really stayed in touch",
        "7": "friend - but more a friend of friends",
        "8": "family, less close",
        "9": "acquaintence, have only met a few times",
        "10": "never met"
    }
    
    # Process people data into dictionaries
    people_data = {}
    people_by_email = {}
    people_count = 0
    
    for row in rows:
        # Pad any missing columns
        padded_row = row + [''] * (6 - len(row))
        name, email, nickname, they_call_me, relationship, rel_level = padded_row[:6]
        
        # Skip rows where name is blank
        if not name.strip():
            continue
            
        person_info = {
            'name': name.strip(),
            'email': email.strip(),
            'nickname': nickname.strip(),
            'they_call_me': they_call_me.strip(),
            'relationship': relationship.strip(),
            'relationship_level': rel_level.strip() if rel_level.strip().isdigit() else '10'
        }
        
        # Index by name (case insensitive)
        people_data[name.strip().lower()] = person_info
        
        # Also index by email for lookup
        if email.strip():
            people_by_email[email.strip().lower()] = person_info
        
        people_count += 1
    
    logging.info(f"Retrieved {len(rows)} total rows and added {people_count} people entries from Google Sheets")
    
    # Return the dictionaries of people data and relationship levels
    return people_data, people_by_email, relationship_levels

# For testing locally
if __name__ == "__main__":
    people_data, people_by_email, relationship_levels = get_people_from_sheet()
    print(f"Retrieved {len(people_data)} people")
    print("Relationship levels:", relationship_levels)