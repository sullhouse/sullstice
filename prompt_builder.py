import logging
from data_loader import load_event_details, load_previous_event, load_current_lineup

def format_rsvp_summary(rsvp_data):
    """
    Format RSVP data into a summary for the AI prompt
    
    Args:
        rsvp_data: Dictionary with RSVP information
        
    Returns:
        String containing formatted RSVP summary
    """
    name = rsvp_data.get("name", "Guest")
    email = rsvp_data.get("email", "")
    arriving = rsvp_data.get("arriving", "").capitalize()
    departing = rsvp_data.get("departing", "").capitalize()
    camping = rsvp_data.get("camping", "")
    other_guests = rsvp_data.get("other_guests", "")
    notes = rsvp_data.get("notes", "")
    questions = rsvp_data.get("questions", "")
    
    return f"""
Name: {name}
Email: {email}
Arriving: {arriving}
Departing: {departing}
Camping preference: {camping}
Other guests: {other_guests}
Notes: {notes}
Questions: {questions}
"""

def build_rsvp_attending_prompt(rsvp_data, personalization, relationship_context, relationship_levels_text):
    """
    Build prompt for OpenAI when the person is attending
    
    Args:
        rsvp_data: Dictionary with RSVP information
        personalization: Dictionary with person's info
        relationship_context: String with relationship context
        relationship_levels_text: String with relationship levels description
        
    Returns:
        String containing the prompt
    """
    # Get event information
    event_details = load_event_details()
    previous_event = load_previous_event()
    current_lineup = load_current_lineup()
    
    # Format RSVP summary
    rsvp_summary = format_rsvp_summary(rsvp_data)
    
    return f"""
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
2a. If they are arriving and departing same day, they aren't camping and we don't need to mention anything about camping or rv
3. Addresses any notes or questions they included (if applicable)
4. Provides relevant information from the event details based on their camping choice, arrival day, etc.
5. If appropriate, mentions activities or performances from this year's lineup that might interest them
5a. Tell them that the schedule is still being finalized and to check the website for updates
6. If we're close (relationship level 1-3), include a personal touch or inside reference that feels authentic
7. If it's someone I haven't seen in a while (level 3, 5, or 6), express that I'm looking forward to catching up
8. If it's family, use an appropriate familial tone
9. Sign off with my name as {personalization['they_call_me']}

Format the body as "BODY: Your email body here"

The response should be conversational, reflecting the actual relationship I have with this person. Make it sound like it was written by me, not by an AI.
"""

def build_rsvp_not_attending_prompt(rsvp_data, personalization, relationship_context, relationship_levels_text):
    """
    Build prompt for OpenAI when the person is not attending
    
    Args:
        rsvp_data: Dictionary with RSVP information
        personalization: Dictionary with person's info
        relationship_context: String with relationship context
        relationship_levels_text: String with relationship levels description
        
    Returns:
        String containing the prompt
    """
    # Get event information
    event_details = load_event_details()
    previous_event = load_previous_event()
    
    # Format RSVP summary
    rsvp_summary = format_rsvp_summary(rsvp_data)
    
    return f"""
You are responding to an RSVP decline for Sullstice, a multi-day camping event. Use a friendly, casual, 
and understanding tone appropriate for the specific relationship with this person.

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

Create two parts: An email subject line and a body.

For the subject line:
- Create a brief, personalized subject line acknowledging their Sullstice RSVP
- Include their name if appropriate
- Keep it under 60 characters
- Format it as "SUBJECT: Your subject line here"

For the body:
Write a personalized email response to {personalization['nickname']} that:
1. Expresses understanding and appreciation that they took the time to RSVP even though they can't attend
2. Conveys that they'll be missed this year
3. Reminds them that Sullstice happens every year around the same time (Memorial Day weekend) and you hope to see them next year
4. Addresses any notes or questions they included (if applicable)
5. If we're close (relationship level 1-3), include a personal touch or inside reference that feels authentic
6. If it's family, use an appropriate familial tone
7. Sign off with my name as {personalization['they_call_me']}

Format the body as "BODY: Your email body here"

The response should be conversational, reflecting the actual relationship I have with this person. Make it sound like it was written by me, not by an AI.
"""

def build_question_prompt(question):
    """
    Build prompt for answering a general question about Sullstice
    
    Args:
        question: String containing the question
        
    Returns:
        String containing the prompt
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
    
    return f"""Here is information about Sullstice:\n{context}\n\nPlease answer this question: {question}"""
