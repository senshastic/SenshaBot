import re
from datetime import datetime, timedelta

def parse_duration(input_str: str):
    now = datetime.now()

    # tests is bad 
    input_str = input_str.lower().strip()

    if input_str == "tomorrow":
        return now + timedelta(days=1)

    # 
    duration_patterns = {
        'days': r'(\d+)\s?d',       # e.g., "2d" for 2 days
        'hours': r'(\d+)\s?h',      # e.g., "3h" for 3 hours
        'minutes': r'(\d+)\s?m',    # e.g., "5m" for 5 minutes
        'seconds': r'(\d+)\s?s'     # e.g., "10s" for 10 seconds
    }

    days = hours = minutes = seconds = 0

    # Check each pattern and extract the relevant number if it matches
    for unit, pattern in duration_patterns.items():
        match = re.search(pattern, input_str)
        if match:
            if unit == 'days':
                days += int(match.group(1)) 
            elif unit == 'hours':
                hours += int(match.group(1))  
            elif unit == 'minutes':
                minutes += int(match.group(1))  
            elif unit == 'seconds':
                seconds += int(match.group(1))  

    # If no valid duration part is found, raise an error
    if days == 0 and hours == 0 and minutes == 0 and seconds == 0:
        raise ValueError(f"Invalid duration format: '{input_str}'")

    # Return the future time by adding the parsed timedelta to the current time
    remind_time = now + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    return remind_time
