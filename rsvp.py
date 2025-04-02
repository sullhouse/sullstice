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

def update_rsvp_in_bigquery(rsvp_id, ai_response):
    """
    Update the RSVP entry in BigQuery with the AI response
    
    Args:
        rsvp_id: The unique ID of the RSVP entry
        ai_response: The AI-generated response to update
    """
    try:
        # Define the table reference
        table_ref = bigquery_client.dataset("guests").table("rsvp")
        
        # Define the update query
        query = f"""
        UPDATE `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}`
        SET ai_response = @ai_response
        WHERE id = @rsvp_id
        """
        
        # Execute the query with parameters
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ai_response", "STRING", ai_response),
                bigquery.ScalarQueryParameter("rsvp_id", "STRING", rsvp_id),
            ]
        )
        query_job = bigquery_client.query(query, job_config=job_config)
        query_job.result()  # Wait for the query to complete
        print("RSVP entry updated with AI response in BigQuery")
    except Exception as e:
        print(f"Error updating RSVP in BigQuery: {str(e)}")

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
        
        # Prepare the initial RSVP data
        rsvp_data = {
            "can_attend": can_attend,
            "name": name,
            "email": email,
            "other_guests": other_guests,
            "arriving": arriving,
            "departing": departing,
            "camping": camping,
            "notes": notes,
            "questions": questions,
        }
        
        # Send an initial email with the RSVP details
        initial_email_subject = f"New RSVP Received: {name}"
        initial_email_body = (
            f"RSVP Details:\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Can Attend: {can_attend}\n"
            f"Other Guests: {other_guests}\n"
            f"Arriving: {arriving}\n"
            f"Departing: {departing}\n"
            f"Camping: {camping}\n"
            f"Notes: {notes}\n"
            f"Questions: {questions}\n"
        )
        aws_email.send_email(
            initial_email_subject,
            initial_email_body,
            "sullhouse@gmail.com",
            None,  # No CC for the initial email
            None,  # No Reply-To for the initial email
            "sullstice-ai-assistant@sullstice.com"
        )
        
        # Store the RSVP data in BigQuery (without AI response)
        store_rsvp_in_bigquery(rsvp_data)
        
        # Use the AI module to generate a personalized response
        ai_response = sullstice_ai.generate_rsvp_response(request_json)
        
        # Extract subject and body from the AI response
        email_subject = ai_response.get("subject", "Sullstice RSVP")
        email_body = ai_response.get("body", "")
        
        # Send the final confirmation email with the AI response
        aws_email.send_email(
            email_subject, 
            email_body, 
            email, 
            "sullhouse@gmail.com",
            "sullhouse@gmail.com",
            "sullstice-ai-assistant@sullstice.com"
        )
        
        # Update the BigQuery entry with the AI response
        rsvp_id = rsvp_data.get("id")
        update_rsvp_in_bigquery(rsvp_id, email_body)
        
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

        return response_json
    else:
        # Handle non-JSON requests
        return "Request is not a JSON object"