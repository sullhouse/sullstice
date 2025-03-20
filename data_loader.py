import logging
import os
import json
from get_people_from_sheet import get_people_from_sheet
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth import default

def load_file(filepath, error_message):
    """
    Load content from a file with error handling
    
    Args:
        filepath: Path to the file
        error_message: Message to log if loading fails
        
    Returns:
        String containing the file content or error message
    """
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception as e:
        logging.error(f"{error_message}: {e}")
        return ""

def get_doc_content(doc_id):
    """
    Get content from a Google Doc
    
    Args:
        doc_id: The ID of the Google Doc
        
    Returns:
        String containing the document content
    """
    try:
        # Configure the connection
        SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
        
        # Check if we're in test mode
        is_test_mode = os.environ.get('SULLSTICE_TEST_MODE', 'False').lower() == 'true'
        
        if is_test_mode:
            # In test mode, use the service account file
            logging.info("Running in test mode, using service account file")
            SERVICE_ACCOUNT_FILE = 'sullstice-a60fa1da2edb.json'
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        else:
            # In production, rely on the service account running the app
            logging.info("Running in production mode, using default credentials")
            credentials, project = default(scopes=SCOPES)
        
        # Build the service with the appropriate credentials
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Get the document content
        document = docs_service.documents().get(documentId=doc_id).execute()
        doc_content = document.get('body').get('content')
        
        # Extract text from the document
        text = ""
        for element in doc_content:
            if 'paragraph' in element:
                for paragraph_element in element.get('paragraph').get('elements'):
                    if 'textRun' in paragraph_element:
                        text += paragraph_element.get('textRun').get('content')
        
        return text
    except Exception as e:
        logging.error(f"Error fetching Google Doc content: {e}")
        return ""

def load_event_details():
    """
    Load current event details from Google Docs
    """
    EVENT_DETAILS_DOC_ID = '1luRVbRCQOK31oI4mrfNDJUX7-Pc1yv6ZotgduwpKZ8A' # Replace with your actual Doc ID
    content = get_doc_content(EVENT_DETAILS_DOC_ID)
    return content

def load_previous_event():
    """
    Load information about the previous year's event from Google Docs
    """
    PREVIOUS_EVENT_DOC_ID = '1EnXvBT-ehH5eM2txjU5fG6aTofgw8MwvZ540UMOUWNs' # Replace with your actual Doc ID
    content = get_doc_content(PREVIOUS_EVENT_DOC_ID)
    return content

def load_current_lineup():
    """
    Load information about the current year's lineup and activities from Google Docs
    """
    CURRENT_LINEUP_DOC_ID = '1pVbeaffYThcj71rdIAi8AfcYCyv_UyuY_0ylUadTWyA' # Replace with your actual Doc ID
    content = get_doc_content(CURRENT_LINEUP_DOC_ID)
    return content

def get_people_data():
    """
    Get the latest people information directly from the Google Sheet
    
    Returns:
        Tuple containing people data dictionaries and relationship levels
    """
    try:
        # Pass the test mode flag to get_people_from_sheet
        is_test_mode = os.environ.get('SULLSTICE_TEST_MODE', 'False').lower() == 'true'
        people_data, people_by_email, relationship_levels = get_people_from_sheet(is_test_mode)
        return people_data, people_by_email, relationship_levels
    except Exception as e:
        logging.error(f"Error loading people information from sheet: {e}")
        return {}, {}, {}
