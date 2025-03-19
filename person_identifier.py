from data_loader import get_people_data

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

def build_person_context(rsvp_data):
    """
    Get personalization and guest information based on RSVP data
    
    Args:
        rsvp_data: Dictionary containing RSVP information
        
    Returns:
        Tuple containing personalization dict, guest info list, and relationship levels
    """
    # Get people data from sheet
    people_data, people_by_email, relationship_levels = get_people_data()
    
    # Extract RSVP information
    name = rsvp_data.get("name", "Guest")
    email = rsvp_data.get("email", "")
    other_guests = rsvp_data.get("other_guests", "")
    
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
                
    return personalization, guest_info, relationship_levels

def format_relationship_context(personalization, guest_info, relationship_levels):
    """
    Format relationship context for use in prompt
    
    Args:
        personalization: Dictionary with main person's data
        guest_info: List of dictionaries with guests' data
        relationship_levels: Dictionary mapping level to description
        
    Returns:
        Tuple containing relationship context and levels text
    """
    # Build relationship levels description
    relationship_levels_text = "\n".join([f"{level} = {description}" for level, description in relationship_levels.items()])
    
    # Add relationship context
    relationship_context = f"""
Relationship with {personalization['name']}:
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
            
    return relationship_context, relationship_levels_text
