import re

def parse_roleid(role_input: str) -> int:
    # Replace all escaped HTML characters with actual ones
    role_input = role_input.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")

    # Check if the input is a direct role ID (17-19 digits)
    if re.fullmatch(r'\d{17,19}', role_input):
        return int(role_input)

    # Use regex to match role mention like <@&1284577275559546921>
    role_id_match = re.search(r'<@&(\d{17,19})>', role_input)
    
    if role_id_match:
        return int(role_id_match.group(1))  # Return the matched role ID

    # If no valid role ID is found, raise an error
    raise ValueError(f"{role_input} is not a valid role ID or mention")