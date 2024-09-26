import inspect
import sys
import time
import json 
import re 

import discord

from bot import ModerationBot
from commands.base import Command
from commands.dm import DMCommand
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (author_is_mod, is_integer,
                                    is_valid_duration, parse_duration)


from helpers.emoji_parser import parse_emotes

import pandas as pd

class ListUsersCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "listusers"
        self.client = client_instance
        self.storage = client_instance.storage  # Ensure storage is initialized
        self.users_file = "users.json"  # Path to the users JSON file

        # Initialize the JSON file if it doesn't exist
        try:
            with open(self.users_file, "r") as file:
                self.users_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.users_data = {}
            with open(self.users_file, "w") as file:
                json.dump(self.users_data, file)

    def save_users_data(self) -> None:
        """Save the current user data to the JSON file."""
        with open(self.users_file, "w") as file:
            json.dump(self.users_data, file, indent=4)

    def convert_to_csv(self, guild_name: str, user_count: int) -> str:
        """Convert the JSON user data to CSV format."""
        # Extract the current guild's users data
        guild_users_data = self.users_data[guild_name]

        # Convert to DataFrame
        df = pd.DataFrame.from_dict(guild_users_data, orient="index").reset_index()
        df.columns = ["User ID", "Username", "Display Name", "Roles"]

        # Generate CSV filename using guild name and user count
        csv_filename = f"users_list{user_count}{guild_name}.csv"
        df.to_csv(csv_filename, index=False)

        return csv_filename

    async def execute(self, message: discord.Message, **kwargs) -> None:
        guild = message.guild
        guild_name = guild.name.replace(" ", "_")  # Replace spaces with underscores in the guild name
        guild_id = str(guild.id)  # Get guild ID to store data for each guild
        user_count = len(guild.members)  # Get the number of users in the server

        # Ensure the guild entry exists in the JSON data
        if guild_name not in self.users_data:
            self.users_data[guild_name] = {}

        # Store user ID, username, display name, and roles for each member in the guild
        for member in guild.members:
            user_id = str(member.id)
            username = member.name  # Actual username
            display_name = member.display_name  # Display name (nickname or username)

            # Get the roles of the user (excluding @everyone)
            roles = [role.name for role in member.roles if role.name != "@everyone"]

            self.users_data[guild_name][user_id] = {
                "username": username,
                "display_name": display_name,
                "roles": roles
            }

        # Save the updated user data to file
        self.save_users_data()

        # Convert user data to CSV and get the file name
        csv_filename = self.convert_to_csv(guild_name, user_count)
        
        # Send a confirmation message with the number of users
        await message.channel.send(f"List of {user_count} users compiled in `users.json`. Converted to and saved as `{csv_filename}`.")




# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
