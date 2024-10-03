import re

def parse_attachments(response):
    """Parse the message content and replace escaped attachment links with the correct Discord format."""
    # Replace escaped HTML characters with actual ones
    response = response.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    
    # Regex to match any attachment link with "cdn.discordapp.com/attachments/"
    attachment_pattern = re.compile(r"https:\/\/cdn\.discordapp\.com\/attachments\/\d+\/\d+\/[^\s<]+")
    
    # Ensure any matches are correctly formatted (without escaped characters)
    parsed_response = re.sub(attachment_pattern, lambda match: match.group(0), response)
    
    return parsed_response
