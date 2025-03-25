import logging
from data_loader import load_updated_event_details
from html_generator import generate_details_html
from flask import Response

def main(request):
    """
    Handle requests for updated event details HTML
    
    Args:
        request: Flask request object
        
    Returns:
        HTML content as a response
    """
    try:
        # Get the updated content from Google Docs
        doc_content = load_updated_event_details()
        
        if not doc_content:
            return {"error": "Could not load document content"}, 500
        
        # Generate the HTML content using the new generator function
        html_content = generate_details_html(doc_content)
        
        # Return HTML response
        return Response(html_content, mimetype='text/html')
    
    except Exception as e:
        logging.error(f"Error handling updated details request: {e}")
        return {"error": str(e)}, 500
