import os
import openai
import logging
import re
from get_people_from_sheet import get_people_from_sheet

# Initialize OpenAI API key from environment variable
# Make sure to set OPENAI_API_KEY in your environment
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logging.warning("OPENAI_API_KEY environment variable not set. OpenAI functions will fail.")
openai.api_key = api_key

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

def identify_person(name_or_email, people_data, people_by_email):
    """
    Try to identify a person by name or email
    
    Args:
        name_or_email: String with person's name or email
        people_data: Dictionary of people indexed by name
        people_by_email: Dictionary of people indexed by email
        
    Returns:
        Dictionary with person's info or None if not found
    """
    if not name_or_email:
        return None
        
    # Try exact email match
    if '@' in name_or_email:
        email = name_or_email.strip().lower()
        if email in people_by_email:
            return people_by_email[email]
    
    # Try name match
    name = name_or_email.strip().lower()
    if name in people_data:
        return people_data[name]
    
    # Try partial name match (first name)
    for person_name, person_info in people_data.items():
        if name in person_name or person_name in name:
            return person_info
            
    return None

def generate_rsvp_response(rsvp_data):
    """
    Generate a personalized response to an RSVP using OpenAI
    
    Args:
        rsvp_data: Dictionary containing RSVP information
        
    Returns:
        Dictionary containing the AI-generated response with subject and body
    """
    # Load all context information
    event_details = load_event_details()
    previous_event = load_previous_event()
    current_lineup = load_current_lineup()
    people_data, people_by_email, relationship_levels = get_people_data()
    
    # Extract RSVP information
    name = rsvp_data.get("name", "Guest")
    email = rsvp_data.get("email", "")
    arriving = rsvp_data.get("arriving", "").capitalize()
    departing = rsvp_data.get("departing", "").capitalize()
    camping = rsvp_data.get("camping", "")
    other_guests = rsvp_data.get("other_guests", "")
    notes = rsvp_data.get("notes", "")
    questions = rsvp_data.get("questions", "")
    
    # Try to identify the person who submitted the RSVP
    person_info = identify_person(email, people_data, people_by_email) or identify_person(name, people_data, people_by_email)
    
    # Prepare personalized information
    personalization = {}
    if person_info:
        personalization = {
            'name': person_info['name'],
            'nickname': person_info['nickname'] if person_info['nickname'] else person_info['name'].split()[0],
            'they_call_me': person_info['they_call_me'] if person_info['they_call_me'] else 'Andrew',
            'relationship': person_info['relationship'],
            'relationship_level': person_info['relationship_level']
        }
    else:
        # Default values if person not found
        personalization = {
            'name': name,
            'nickname': name.split()[0],
            'they_call_me': 'Andrew',
            'relationship': 'Friend',
            'relationship_level': '9'
        }
        
    # Look up guests in the people database
    guest_info = []
    if other_guests:
        guest_names = [g.strip() for g in other_guests.split(',')]
        for guest_name in guest_names:
            guest = identify_person(guest_name, people_data, people_by_email)
            if guest:
                guest_info.append({
                    'name': guest['name'],
                    'nickname': guest['nickname'] if guest['nickname'] else guest['name'].split()[0],
                    'relationship': guest['relationship'],
                    'relationship_level': guest['relationship_level']
                })
            else:
                # Guest not found in database
                guest_info.append({
                    'name': guest_name,
                    'nickname': guest_name.split()[0],
                    'relationship': 'Unknown',
                    'relationship_level': '10'
                })
    
    # Build relationship levels description
    relationship_levels_text = "\n".join([f"{level} = {description}" for level, description in relationship_levels.items()])
    
    # Build RSVP summary for context
    rsvp_summary = f"""
Name: {name}
Email: {email}
Arriving: {arriving}
Departing: {departing}
Camping preference: {camping}
Other guests: {other_guests}
Notes: {notes}
Questions: {questions}
"""

    # Add relationship context
    relationship_context = f"""
Relationship with {name}:
- They call me: {personalization['they_call_me']}
- Nickname or how I refer to them: {personalization['nickname']}
- Our relationship: {personalization['relationship']}
- Relationship level (1-10 where 1 is closest): {personalization['relationship_level']}
"""

    # Add guest relationship context
    if guest_info:
        relationship_context += "\nRelationship with guests:\n"
        for guest in guest_info:
            relationship_context += f"- {guest['name']} (nickname: {guest['nickname']}): {guest['relationship']}, level {guest['relationship_level']}\n"

    # Create the prompt for OpenAI
    prompt = f"""
You are responding to an RSVP for Sullstice, a multi-day camping event. Use a friendly, casual, 
and informative tone appropriate for the specific relationship with this person.

Here's information about the RSVP:
{rsvp_summary}

Important personal context to help personalize this response:
{relationship_context}

Relationship level meanings:
{relationship_levels_text}

Here are the event details for reference:
{event_details}

Information about the previous Sullstice event (2024):
{previous_event}

Information about the current year's lineup and activities:
{current_lineup}

Create two parts: An email subject line and a body.

For the subject line:
- Create a brief, personalized subject line related to their Sullstice RSVP
- Include their name if appropriate
- Keep it under 60 characters
- Format it as "SUBJECT: Your subject line here"

For the body:
Write a personalized email response to {personalization['nickname']} that:
1. Shows genuine excitement about seeing them (and their guests) at Sullstice, with the tone matching our relationship and relationship level
2. Confirms their RSVP details (arrival/departure days, camping preference, additional guests)
3. Addresses any notes or questions they included (if applicable)
4. Provides relevant information from the event details based on their camping choice, arrival day, etc.
5. If appropriate, mentions activities or performances from this year's lineup that might interest them
6. If we're close (relationship level 1-3), include a personal touch or inside reference that feels authentic
7. If it's someone I haven't seen in a while (level 3, 5, or 6), express that I'm looking forward to catching up
8. If it's family, use an appropriate familial tone
9. Sign off with my name as {personalization['they_call_me']}

Format the body as "BODY: Your email body here"

The response should be conversational, reflecting the actual relationship I have with this person. Make it sound like it was written by me, not by an AI.
"""

    try:
        # Check if API key is available before calling the OpenAI API
        if not api_key:
            raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
        
        # Call OpenAI API
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",  # Upgrade to GPT-4 for better personalization
            messages=[
                {"role": "system", "content": f"You are the host of Sullstice. Your name is {personalization['they_call_me']} (Andrew Sullivan), writing a personalized RSVP response."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        
        # Extract and parse the generated response
        ai_response = response.choices[0].message.content.strip()
        
        # Extract subject and body
        subject_match = re.search(r"SUBJECT:\s*(.*?)(?=$|\s*BODY:)", ai_response, re.DOTALL)
        body_match = re.search(r"BODY:\s*(.*?)$", ai_response, re.DOTALL)
        
        subject = "Your Sullstice RSVP Confirmation"  # Default subject
        body = ai_response  # Default to full response if parsing fails
        
        if subject_match:
            subject = subject_match.group(1).strip()
        
        if body_match:
            body = body_match.group(1).strip()
        
        body += f"\n\nP.S. This response came from Sullstice AI. Hopefully it was pretty good. No worries though, I'm cc'd on this email and read every one."
        
        return {
            "subject": subject,
            "body": body
        }
    
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        
        # Fallback response if AI fails
        subject = f"Sullstice RSVP Confirmation for {personalization['nickname']}"
        
        body = f"Hi {personalization['nickname']},\n\n"
        body += f"""Thank you for your RSVP to Sullstice! I've got you down for the following:

Arriving: {arriving}
Departing: {departing}
Camping option: {camping}
"""
        if other_guests:
            body += f"Additional guests: {other_guests}\n"
        if notes:
            body += f"Your notes: {notes}\n"
            
        body += """
Please visit sullstice.com for event details and updates.

Looking forward to seeing you!
"""
        body += personalization['they_call_me']
        
        return {
            "subject": subject,
            "body": body
        }

def answer_question(question):
    """
    Generate a specific answer to a question about Sullstice
    
    Args:
        question: String containing the question
        
    Returns:
        String containing the answer
    """
    # Load all available context
    event_details = load_event_details()
    previous_event = load_previous_event()
    current_lineup = load_current_lineup()
    
    # Combine context with preference for current year information
    context = f"""
GENERAL EVENT INFORMATION FOR THIS YEAR:
{event_details}

CURRENT YEAR'S LINEUP AND ACTIVITIES:
{current_lineup}

INFORMATION ABOUT LAST YEAR'S EVENT (2024) - Use this for reference if the question isn't clearly answered by current year information:
{previous_event}
"""
        
    try:
        # Check if API key is available before calling the OpenAI API
        if not api_key:
            raise ValueError("OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable.")
            
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",  # Upgraded to GPT-4 for better question answering
            messages=[
                {"role": "system", "content": """You are a helpful assistant for Sullstice, a multi-day camping event. 
When answering questions:
1. Prioritize information from the current year's details and lineup
2. If the current year's information doesn't fully address the question, you can reference how things worked in 2024, but clearly indicate that this is historical information and things might be different this year
3. Be conversational and friendly in your tone
4. Be concise but thorough
5. If the question is about something not mentioned in any of the provided information, acknowledge this and suggest contacting Andrew directly at sullhouse@gmail.com"""},
                {"role": "user", "content": f"Here is information about Sullstice:\n{context}\n\nPlease answer this question: {question}"}
            ],
            max_tokens=500,
            temperature=0.5,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logging.error(f"Error generating answer to question: {e}")
        return "I couldn't find specific information about that. Please email sullhouse@gmail.com for more details."
