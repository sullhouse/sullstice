import aws_email
import sullstice_ai
from google.cloud import bigquery
import uuid
from datetime import datetime

# Initialize BigQuery client
bigquery_client = bigquery.Client()

def store_rsvp_in_bigquery(rsvp_data):
    """
    Store RSVP data in BigQuery
    
    Args:
        rsvp_data: Dictionary containing RSVP information
    """
    try:
        # Add timestamp and unique ID
        rsvp_data["id"] = str(uuid.uuid4())
        rsvp_data["timestamp"] = datetime.now().isoformat()
        
        # Define the table reference
        table_ref = bigquery_client.dataset("guests").table("rsvp")
        
        # Insert the row
        errors = bigquery_client.insert_rows_json(table_ref, [rsvp_data])
        
        if errors:
            print(f"Encountered errors while inserting row: {errors}")
        else:
            print("RSVP data inserted into BigQuery")
    except Exception as e:
        print(f"Error storing RSVP in BigQuery: {str(e)}")

def main(request):
    if request.is_json:
        # Get the JSON data
        request_json = request.get_json()
        
        # Extract data from the request using the new format
        can_attend = request_json.get("can_attend", "yes").lower()  # Normalize to lowercase
        name = request_json.get("name", "Guest")
        email = request_json.get("email", "")
        other_guests = request_json.get("other_guests", "")
        arriving = request_json.get("arriving", "")
        departing = request_json.get("departing", "")
        camping = request_json.get("camping", "")
        notes = request_json.get("notes", "")
        questions = request_json.get("questions", "")
        
        # Ensure can_attend is set in the data passed to the AI
        request_json["can_attend"] = can_attend
        
        # Use the AI module to generate a personalized response
        ai_response = sullstice_ai.generate_rsvp_response(request_json)
        
        # Extract subject and body from the AI response
        email_subject = ai_response.get("subject", "Sullstice RSVP")
        email_body = ai_response.get("body", "")
        
        # Send confirmation email
        aws_email.send_email(
            email_subject, 
            email_body, 
            email, 
            "sullhouse@gmail.com",
            "sullhouse@gmail.com",
            "sullstice-ai-assistant@sullstice.com"
        )

        # Return confirmation to API caller
        response_json = {
            "can_attend": can_attend,
            "name": name,
            "email": email,
            "other_guests": other_guests,
            "arriving": arriving,
            "departing": departing,
            "camping": camping,
            "notes": notes,
            "questions": questions,
            "status": "RSVP received successfully",
            "email_subject": email_subject,
            "ai_response": email_body
        }
        
        # Store RSVP data in BigQuery
        store_rsvp_in_bigquery(response_json)

        return response_json
    else:
        # Handle non-JSON requests
        return "Request is not a JSON object"