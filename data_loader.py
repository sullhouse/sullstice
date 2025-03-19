import logging
from get_people_from_sheet import get_people_from_sheet

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

def load_event_details():
    """
    Load current event details from the event_details.txt file
    """
    return load_file("event_details.txt", "Error loading event details")

def load_previous_event():
    """
    Load information about the previous year's event
    """
    return load_file("sullstice_2024.txt", "Error loading 2024 event information")

def load_current_lineup():
    """
    Load information about the current year's lineup and activities
    """
    return load_file("sullstice_2025_lineup.txt", "Error loading 2025 lineup information")

def get_people_data():
    """
    Get the latest people information directly from the Google Sheet
    
    Returns:
        Tuple containing people data dictionaries and relationship levels
    """
    try:
        people_data, people_by_email, relationship_levels = get_people_from_sheet()
        return people_data, people_by_email, relationship_levels
    except Exception as e:
        logging.error(f"Error loading people information from sheet: {e}")
        return {}, {}, {}
