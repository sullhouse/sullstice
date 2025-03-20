import os
import openai
import logging
import re
from person_identifier import build_person_context, format_relationship_context
from prompt_builder import build_rsvp_attending_prompt, build_rsvp_not_attending_prompt, build_question_prompt

def get_openai_api_key():
    # Get OpenAI API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logging.warning("OPENAI_API_KEY environment variable not set. OpenAI functions will fail.")
    openai.api_key = api_key
    return api_key

def generate_rsvp_response(rsvp_data):
    """
    Generate a personalized response to an RSVP using OpenAI
    
    Args:
        rsvp_data: Dictionary containing RSVP information
        
    Returns:
        Dictionary containing the AI-generated response with subject and body
    """
    # Get attendance status
    can_attend = rsvp_data.get("can_attend", "yes").lower() == "yes"
    
    # Get person and relationship information
    personalization, guest_info, relationship_levels = build_person_context(rsvp_data)
    relationship_context, relationship_levels_text = format_relationship_context(
        personalization, guest_info, relationship_levels
    )

    # Build appropriate prompt based on attendance
    if can_attend:
        prompt = build_rsvp_attending_prompt(
            rsvp_data, personalization, relationship_context, relationship_levels_text
        )
    else:
        prompt = build_rsvp_not_attending_prompt(
            rsvp_data, personalization, relationship_context, relationship_levels_text
        )

    try:
        # Check if API key is available before calling the OpenAI API
        api_key = get_openai_api_key()
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
        
        body += f"\n\nP.S. This response came from Sullstice AI. Hopefully it was pretty good. It made have made some stuff up. No worries though, I'm cc'd on the email and read every one."
        
        return {
            "subject": subject,
            "body": body
        }
    
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        
        # Fallback response if AI fails
        if can_attend:
            subject = f"Sullstice RSVP Confirmation for {personalization['nickname']}"
            
            body = f"Hi {personalization['nickname']},\n\n"
            body += f"""Thank you for your RSVP to Sullstice! I've got you down for the following:

Arriving: {rsvp_data.get('arriving', '')}
Departing: {rsvp_data.get('departing', '')}
Camping option: {rsvp_data.get('camping', '')}
"""
            if rsvp_data.get('other_guests', ''):
                body += f"Additional guests: {rsvp_data.get('other_guests', '')}\n"
            if rsvp_data.get('notes', ''):
                body += f"Your notes: {rsvp_data.get('notes', '')}\n"
                
            body += """
Please visit sullstice.com for event details and updates.

Looking forward to seeing you!
"""
        else:
            subject = f"Sorry you can't make it to Sullstice, {personalization['nickname']}"
            
            body = f"Hi {personalization['nickname']},\n\n"
            body += """Thank you for letting me know you won't be able to make it to Sullstice this year. You'll be missed!

Remember that we do this event every summer solstice, so hopefully you can join us next year.
"""
            if rsvp_data.get('notes', ''):
                body += f"\nRegarding your notes: {rsvp_data.get('notes', '')}\n"
        
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
    # Check if API key is available before proceeding
    api_key = get_openai_api_key()
    if not api_key:
        logging.warning("OPENAI_API_KEY environment variable not set. OpenAI functions will fail.")
        return "I couldn't access the necessary information to answer your question. Please email sullhouse@gmail.com for assistance."
    
    # Build the prompt using the function from prompt_builder
    prompt = build_question_prompt(question)
        
    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",  # Upgraded to GPT-4 for better question answering
            messages=[
                {"role": "system", "content": """You are a helpful assistant for Sullstice, a multi-day camping event. 
When answering questions:
1. Prioritize information from the current year's details and lineup that are being pulled from live Google Docs
2. If the current year's information doesn't fully address the question, you can reference how things worked in 2024, but clearly indicate that this is historical information and things might be different this year
3. Be conversational and friendly in your tone
4. Be concise but thorough
5. If the question is about something not mentioned in any of the provided information, acknowledge this and suggest contacting Andrew directly at sullhouse@gmail.com"""},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5,
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logging.error(f"Error generating answer to question: {e}")
        return "I couldn't find specific information about that. Please email sullhouse@gmail.com for more details."
