import os
import openai
import logging

# Initialize OpenAI API key from environment variable
# Make sure to set OPENAI_API_KEY in your environment
openai.api_key = os.environ.get("OPENAI_API_KEY")

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

def generate_rsvp_response(rsvp_data):
    """
    Generate a personalized response to an RSVP using OpenAI
    
    Args:
        rsvp_data: Dictionary containing RSVP information
        
    Returns:
        String containing the AI-generated response
    """
    # Load all context information
    event_details = load_event_details()
    previous_event = load_previous_event()
    current_lineup = load_current_lineup()
    
    # Extract RSVP information
    name = rsvp_data.get("name", "Guest")
    arriving = rsvp_data.get("arriving", "").capitalize()
    departing = rsvp_data.get("departing", "").capitalize()
    camping = rsvp_data.get("camping", "")
    other_guests = rsvp_data.get("other_guests", "")
    notes = rsvp_data.get("notes", "")
    questions = rsvp_data.get("questions", "")
    
    # Build RSVP summary for context
    rsvp_summary = f"""
Name: {name}
Arriving: {arriving}
Departing: {departing}
Camping preference: {camping}
Other guests: {other_guests}
Notes: {notes}
Questions: {questions}
"""

    # Create the prompt for OpenAI
    prompt = f"""
You are responding to an RSVP for Sullstice, a multi-day camping event. Use a friendly, casual, 
and informative tone that matches the writing style in the event details.

Here's information about the RSVP:
{rsvp_summary}

Here are the event details for reference:
{event_details}

Information about the previous Sullstice event (2024):
{previous_event}

Information about the current year's lineup and activities:
{current_lineup}

Write a personalized email response to {name} that:
1. Confirms their RSVP details (arrival/departure days, camping preference, additional guests)
2. Addresses any notes or questions they included (if applicable)
3. Provides relevant information from the event details based on their camping choice, arrival day, etc.
4. If appropriate, mentions activities or performances from this year's lineup that might interest them
5. If they asked about something not specified in the current year's information, you can reference how it worked in 2024, but clarify that this year might be different
6. Maintains a casual, friendly tone that matches the event details writing style
7. Expresses excitement about seeing them at Sullstice

The response should be conversational, like it's written by a friend who's organizing a fun event, not formal or corporate.
"""

    try:
        # Call OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Use GPT-3.5-turbo for low cost
            messages=[
            {"role": "system", "content": "You are the host of Sullstice, your name is Andrew Sullivan, writing personalized RSVP responses."},
            {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        
        # Extract and return the generated response
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        
        # Fallback response if AI fails
        fallback = f"""{name},

Thank you for your RSVP to Sullstice! I've got you down for the following:

Arriving: {arriving}
Departing: {departing}
Camping option: {camping}
"""
        if other_guests:
            fallback += f"Additional guests: {other_guests}\n"
        if notes:
            fallback += f"Your notes: {notes}\n"
            
        fallback += """
Please visit sullstice.com for event details and updates.

Looking forward to seeing you!
Sullhouse
"""
        return fallback

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
        response = openai.chat.completions.create(
            model="gpt-4",  # Upgraded to GPT-4 for better question answering
            messages=[
                {"role": "system", "content": """You are a helpful assistant for Sullstice, a multi-day camping event. 
When answering questions:
1. Prioritize information from the current year's details and lineup
2. If the current year's information doesn't fully address the question, you can reference how things worked in 2024, but clearly indicate that this is historical information and things might be different this year
3. Be conversational and friendly in your tone
4. Be concise but thorough
5. If the question is about something not mentioned in any of the provided information, acknowledge this and suggest contacting the organizers directly at sullhouse@gmail.com"""},
                {"role": "user", "content": f"Here is information about Sullstice:\n{context}\n\nPlease answer this question: {question}"}
            ],
            max_tokens=500,
            temperature=0.5,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logging.error(f"Error generating answer to question: {e}")
        return "I couldn't find specific information about that. Please email sullhouse@gmail.com for more details."
