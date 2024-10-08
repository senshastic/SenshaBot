from typing import Union

from discord import Member

from storage_management import StorageManagement


def is_integer(string: str) -> bool:
    """Checks if the string is an integer

    Args:
        string (str): The string to check

    Returns:
        Boolean: Whether the string could be converted to an integer or not
    """
    try:
        int(string)
        return True
    except ValueError:
        return False


# For compatiblity with existing code. This macro exists so people don't need to update to use `is_integer` in their code
is_number = is_integer


def is_float(string: str) -> bool:
    """Checks if the string is a float

    Args:
        string (str): The string to check

    Returns:
        Boolean: Whether the string could be converted to a float or not
    """
    try:
        float(string)
        return True
    except ValueError:
        return False


def is_valid_duration(duration: Union[int, str]) -> bool:
    """Checks if the duration is a positive number

    Args:
        duration (int, str): The duration to validate

    Returns:
        Boolean: If it is a valid duration
    """
    if is_integer(duration):
        if int(duration) > 0:
            return True
        else:
            return False
    else:
        return False


def parse_duration(string: str) -> int:
    """Parses a duration in seconds from a duration string

    Args:
        s (str): Duration string to parse (1w3d10h30m20s)

    Returns:
        int: The time in seconds of the duration string
    """
    if is_integer(string):
        return int(string)
    else:
        values = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
        nums = []
        tempnums = []
        for char in string:
            if char.isdigit():
                tempnums.append(char)
            elif char == " " or char is None:
                continue
            else:
                multiple = values.get(char, 1)
                try:
                    num = int("".join(tempnums))
                    tempnums.clear()
                    nums.append(num * multiple)
                except ValueError:
                    return -1
        if len(nums) > 0:
            return sum(nums)
        else:
            return -1


def author_is_admin(author: Member) -> bool:
    """Checks if the author is an administrator

    Args:
        author (discord.Member): Discord member object

    Returns:
        Boolean: If they are an administrator
    """
    return author.guild_permissions.administrator


async def author_is_mod(author: Member, storage: StorageManagement) -> bool:
    """Checks if the author is a mod or administrator

    Args:
        author (discord.Member): Discord member object
        storage (StorageManagement): Instance of the storage management class

    Returns:
        Boolean: If they are a mod or administrator
    """
    if author_is_admin(author):
        return True
    
    guild_id = str(author.guild.id)
    mod_roles = storage.settings["guilds"][guild_id].get("mod_roles")
    
    if mod_roles is None:
        storage.settings["guilds"][guild_id]["mod_roles"] = []
        await storage.write_file_to_disk()
        mod_roles = storage.settings["guilds"][guild_id].get("mod_roles")

    # Extract the role IDs from the author's roles
    author_role_ids = [role.id for role in author.roles]
    
    # Check if any of the author's role IDs are in the mod_roles list
    return any(role_id in mod_roles for role_id in author_role_ids)

