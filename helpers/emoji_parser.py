import re
import discord

# Reuse the function to parse and replace custom and bot-specific emotes
def parse_emotes(response, client):
    # Access bot-specific custom emojis
    bot_emojis = {emoji.name: emoji for emoji in client.emojis}

    # Pattern to match escaped custom emotes in the format &lt;:emote_name:emote_id&gt; and &lt;a:emote_name:emote_id&gt;
    escaped_emote_pattern = re.compile(r'&lt;(a?):([a-zA-Z0-9_]+):(\d+)&gt;')

    # Function to replace escaped emotes with the correct Discord format
    def replace_emote(match):
        is_animated = match.group(1) == "a"  # Check if it's animated
        emote_name = match.group(2)
        emote_id = match.group(3)
        
        # If the emoji is found in the bot's custom emojis, return the correct format
        if emote_name in bot_emojis:
            if is_animated:
                return f"<a:{emote_name}:{emote_id}>"
            else:
                return f"<:{emote_name}:{emote_id}>"
        else:
            # If the emoji is not recognized, return the fallback :emote_name: format
            return f":{emote_name}:"

    # Replace all escaped emotes in the response
    parsed_response = re.sub(escaped_emote_pattern, replace_emote, response)
    
    return parsed_response