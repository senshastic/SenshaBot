import re

def parse_userid(user_input: str) -> int:
    # Replace escaped HTML characters with actual ones
    user_input = user_input.replace("&lt;", "<").replace("&gt;", ">")

    # Check if the input is a direct user ID (18 digits)
    if re.fullmatch(r'\d{17,19}', user_input):  # Adjust to 17-19 digits for safety
        return int(user_input)

    # Use regex to match mention like <@!123456789012345678> or <@123456789012345678>
    user_id_match = re.search(r'<@!?(\d{17,19})>', user_input)
    
    if user_id_match:
        return int(user_id_match.group(1))  # Return the matched user ID

    # If no valid user ID is found, raise an error
    print(f"No valid user ID found in input: {user_input}")
    raise ValueError(f"{user_input} is not a valid user ID or mention")
