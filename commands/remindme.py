import time
import json
import asyncio
import discord
import inspect
import os 
import sys
from bot import ModerationBot
from commands.base import Command
from datetime import datetime
from helpers.timeframe_parser import parse_duration
from helpers.emoji_parser import parse_emotes

REMINDER_FILE_PATH = "reminders.json"


import asyncio
from datetime import datetime, timedelta
import json
import os

# File path for storing reminders
REMINDER_FILE_PATH = "reminders.json"

class RemindMeCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "remindme"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}remindme <timeframe> \"reminder message\""
        self.invalid_timeframe = "Invalid timeframe format. {usage}"
        self.not_enough_arguments = "You must provide a timeframe and a reminder message. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        if len(command) >= 2:
            # Parse the timeframe and the reminder message
            timeframe = command[0]
            reminder_message = " ".join(command[1:])

            try:
                remind_time = parse_duration(timeframe)
                delay = (remind_time - datetime.now()).total_seconds()

                if delay <= 0:
                    raise ValueError(f"Invalid duration, reminder time is in the past.")

                guild_id = str(message.guild.id)
                user_id = str(message.author.id)

                # Store the reminder in a JSON file
                await self.store_reminder(guild_id, user_id, reminder_message, remind_time, "channel")

                # React with a checkmark
                await message.add_reaction("✅")

                # Schedule the reminder
                asyncio.create_task(self.handle_reminder(message, reminder_message, delay))

            except ValueError:
                await message.reply(self.invalid_timeframe.format(usage=self.usage))
        else:
            await message.reply(self.not_enough_arguments.format(usage=self.usage))

    async def handle_reminder(self, message, reminder_message, delay):
        """Handles the reminder after the specified delay."""
        await asyncio.sleep(delay)
        await message.reply(f"{message.author.mention}, here's your reminder: \"{reminder_message}\"")

    async def store_reminder(self, guild_id, user_id, reminder_message, remind_time, reminder_type):
        """Store the reminder in reminders.json."""
        try:
            with open(REMINDER_FILE_PATH, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"guilds": {}}

        if guild_id not in data["guilds"]:
            data["guilds"][guild_id] = {"reminders": {}}

        if user_id not in data["guilds"][guild_id]["reminders"]:
            data["guilds"][guild_id]["reminders"][user_id] = []

        data["guilds"][guild_id]["reminders"][user_id].append({
            "message": reminder_message,
            "time": remind_time.timestamp(),
            "type": reminder_type
        })

        # Save updated reminders
        with open(REMINDER_FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)


class RemindMeDMCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "remindmedm"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}remindmedm <timeframe> \"reminder message\""
        self.invalid_timeframe = "Invalid timeframe format. {usage}"
        self.not_enough_arguments = "You must provide a timeframe and a reminder message. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        # No moderator check, anyone can set a reminder
        if len(command) >= 2:
            # Parse the timeframe (first argument) and treat the rest as the reminder message
            timeframe = command[0]
            reminder_message = " ".join(command[1:])  # Join everything after the timeframe as the reminder message

            try:
                remind_time = parse_duration(timeframe)
                delay = (remind_time - datetime.now()).total_seconds()

                guild_id = str(message.guild.id)
                user_id = str(message.author.id)

                # Parse the message content to replace custom emojis
                reminder_message = parse_emotes(reminder_message, self.client)

                # Store reminder in the JSON file
                await self.store_reminder(guild_id, user_id, reminder_message, remind_time, "dm")  

                # React with a checkmark
                await message.add_reaction("✅")

                # Create a new asyncio task for the reminder
                asyncio.create_task(self.handle_reminder_dm(message, reminder_message, delay))

            except ValueError:
                await message.reply(self.invalid_timeframe.format(usage=self.usage))
        else:
            await message.reply(self.not_enough_arguments.format(usage=self.usage))

    async def handle_reminder_dm(self, message, reminder_message, delay):
        """Handles the reminder after the specified delay and sends a DM."""
        await asyncio.sleep(delay)
        try:
            # Send the reminder as a DM to the user
            await message.author.send(f"Hello! Here's your reminder: \"{reminder_message}\"")
        except discord.errors.Forbidden:
            # In case the bot can't send a DM (due to privacy settings)
            await message.reply(f"{message.author.mention}, I couldn't send you a DM. Please check your privacy settings.")

    async def store_reminder(self, guild_id, user_id, reminder_message, remind_time, reminder_type):
        """Store the reminder in reminders.json."""
        # Try loading the JSON data, or initialize it if the file does not exist
        try:
            with open(REMINDER_FILE_PATH, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize the JSON structure if file doesn't exist or is corrupted
            data = {"guilds": {}}

        # Ensure the guild structure exists
        if "guilds" not in data:
            data["guilds"] = {}

        # Ensure the guild ID is in the structure
        if guild_id not in data["guilds"]:
            data["guilds"][guild_id] = {"reminders": {}}

        # Ensure the user ID has a reminders list
        if user_id not in data["guilds"][guild_id]["reminders"]:
            data["guilds"][guild_id]["reminders"][user_id] = []

        # Add the reminder data
        data["guilds"][guild_id]["reminders"][user_id].append({
        "message": reminder_message,
        "time": remind_time.timestamp(),
        "type": reminder_type
        })

        # Write the updated data back to the file
        with open(REMINDER_FILE_PATH, "w") as f:
            json.dump(data, f, indent=4)


# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)


class RemindersListCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "reminderslist"
        self.client = client_instance
        self.storage = client_instance.storage
        self.no_reminders = "You don't have any active reminders."

    async def execute(self, message: discord.Message, **kwargs) -> None:
        user_id = str(message.author.id)
        guild_id = str(message.guild.id)
        current_time = datetime.now().timestamp()

        try:
            # Load reminders from JSON file
            with open(REMINDER_FILE_PATH, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"guilds": {}}

        # Check if there are any reminders for this guild and user
        if guild_id in data["guilds"] and user_id in data["guilds"][guild_id]["reminders"]:
            reminders = data["guilds"][guild_id]["reminders"][user_id]

            # Filter out expired reminders
            active_reminders = [r for r in reminders if r["time"] > current_time]

            if active_reminders:
                # Create an embed to display the list of active reminders
                embed = discord.Embed(title=f"Active Reminders for {message.author.name}", color=discord.Color.blue())
                for idx, reminder in enumerate(active_reminders, 1):
                    reminder_type = "DM" if "dm" in reminder.get("type", "").lower() else "Channel"
                    reminder_time = datetime.fromtimestamp(reminder["time"]).strftime("%Y-%m-%d %H:%M:%S")
                    embed.add_field(
                        name=f"Reminder #{idx}",
                        value=f"**Message**: {reminder['message']}\n**Time**: {reminder_time}\n**Type**: {reminder_type}",
                        inline=False
                    )
                
                await message.reply(embed=embed)
            else:
                await message.reply(self.no_reminders)
        else:
            await message.reply(self.no_reminders)



# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
