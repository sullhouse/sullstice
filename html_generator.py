import logging
import re
import os
import html

def parse_document_content(doc_content):
    """
    Parse Google Doc content into structured sections
    
    Args:
        doc_content: Raw text content from Google Doc
        
    Returns:
        Dictionary of sections with headings as keys and content as values
    """
    # Parse the content into sections
    sections = {}
    current_section = "main"
    sections[current_section] = []
    
    lines = doc_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a header line based on patterns like "# Heading" or "## Subheading"
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        
        if header_match:
            level = len(header_match.group(1))
            heading = header_match.group(2).strip()
            current_section = heading
            sections[current_section] = []
        else:
            sections[current_section].append(line)
    
    return sections

def process_markdown_content(content):
    """
    Process markdown content into HTML
    
    Args:
        content: String containing markdown content
        
    Returns:
        String with HTML tags
    """
    # First escape the HTML to prevent injection
    escaped_text = html.escape(content)
    
    # Process bold text (** to <strong>)
    processed = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', escaped_text)
    
    # Process links ([text](url) to <a href="url">text</a>)
    processed = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', processed)
    
    return processed

def generate_details_html(doc_content):
    """
    Generate HTML content for details page based on template and markdown content
    
    Args:
        doc_content: Raw text content from Google Doc in markdown format
        
    Returns:
        String containing the generated HTML
    """
    try:
        # Get the template content with explicit UTF-8 encoding
        template_path = os.path.join(os.path.dirname(__file__), 'web', 'details_template.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Extract the main body content from the template
        body_start = template.find('<body class="prose">')
        body_end = template.find('</body>')
        
        if body_start == -1 or body_end == -1:
            raise ValueError("Could not find body tags in template")
            
        # Find the marker where we'll start replacing content
        replacement_marker = '<h2 id="get_from_google_doc">Get From Google Doc</h2>'
        replacement_start = template.find(replacement_marker)
        if replacement_start == -1:
            raise ValueError("Could not find replacement marker in template")
        
        # Keep the header and main section unchanged
        preserved_content = template[:replacement_start]
        footer = template[body_end:]
        
        # Extract all images from the template for reference
        image_map = {}
        for match in re.finditer(r'<img\s+src="([^"]+)"[^>]*?alt="([^"]+)"[^>]*>', template):
            img_tag = match.group(0)
            alt_text = match.group(2).lower()
            image_map[alt_text] = img_tag
        
        # Process the markdown content
        updated_content = ""
        lines = doc_content.split('\n')
        
        # Track current section state
        current_section = None
        current_subsection = None
        in_list = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                # Close list if we're in one
                if in_list:
                    updated_content += "</ul>\n"
                    in_list = False
                continue
            
            # Check for IMG directive
            img_match = re.match(r'^IMG\s+(.+)$', line)
            if img_match:
                alt_text = img_match.group(1).strip().lower()
                if alt_text in image_map:
                    updated_content += image_map[alt_text] + '\n'
                else:
                    logging.warning(f"Image with alt text '{alt_text}' not found in template")
                continue
            
            # Check for section headers (### SECTION)
            section_match = re.match(r'^###\s+(.+?)(?:\s+###)?$', line)
            if section_match:
                # Close any open list
                if in_list:
                    updated_content += "</ul>\n"
                    in_list = False
                
                section_name = section_match.group(1).strip()
                section_id = section_name.lower().replace(' ', '-').replace('&', 'and')
                current_section = section_name
                current_subsection = None
                
                updated_content += f'<h2 id="{section_id}">{section_name}</h2>\n'
                continue
            
            # Check for subsection headers (## SUBSECTION)
            subsection_match = re.match(r'^##\s+(.+?)(?:\s+##)?$', line)
            if subsection_match:
                # Close any open list
                if in_list:
                    updated_content += "</ul>\n"
                    in_list = False
                
                subsection_name = subsection_match.group(1).strip()
                current_subsection = subsection_name
                
                updated_content += f'<h3>{subsection_name}</h3>\n'
                continue
            
            # Check for bullet points
            if line.startswith('- ') or line.startswith('* '):
                list_content = line[2:].strip()
                processed_content = process_markdown_content(list_content)
                
                if not in_list:
                    updated_content += "<ul>\n"
                    in_list = True
                
                updated_content += f'<li>{processed_content}</li>\n'
            else:
                # Regular paragraph
                if in_list:
                    updated_content += "</ul>\n"
                    in_list = False
                
                processed_content = process_markdown_content(line)
                updated_content += f'<p>{processed_content}</p>\n'
        
        # Close any open list at the end
        if in_list:
            updated_content += "</ul>\n"
        
        # Combine everything
        return preserved_content + updated_content + footer
    
    except Exception as e:
        logging.error(f"Error generating details HTML: {e}")
        return f"<html><body><h1>Error</h1><p>Could not generate page: {str(e)}</p></body></html>"

def generate_updated_details_html(doc_content):
    """
    Alias for the new generate_details_html function for backward compatibility
    """
    return generate_details_html(doc_content)
