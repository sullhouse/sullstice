import aws_email
import sullstice_ai

def main(request):

    if request.is_json:
        # Get the JSON data
        request_json = request.get_json()
        
        # Extract data from the request using the new format
        name = request_json.get("name", "Guest")
        email = request_json.get("email", "")
        other_guests = request_json.get("other_guests", "")
        arriving = request_json.get("arriving", "")
        departing = request_json.get("departing", "")
        camping = request_json.get("camping", "")
        notes = request_json.get("notes", "")
        questions = request_json.get("questions", "")
        
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