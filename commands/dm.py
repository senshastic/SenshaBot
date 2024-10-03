import inspect
import sys
import time
import json
import re

import discord

from bot import ModerationBot
from commands.base import Command
from datetime import datetime
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (
    author_is_mod, 
    is_integer, 
    is_valid_duration, 
    parse_duration
)

from helpers.emoji_parser import parse_emotes
from helpers.userid_parser import parse_userid
from helpers.attachment_parser import parse_attachments

class DMCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "dm"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = (
            f"Usage: {self.client.prefix}dm <user id> **subject** <message>"
        )
        self.invalid_user = (
            "There is no user with the userID: {user_id}. {usage}"
        )
        self.not_enough_arguments = (
            "You must provide a user to DM. {usage}"
        )
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")

        # Check if the author is a moderator
        if not await author_is_mod(message.author, self.storage):
            await message.channel.send("**You must be a moderator to use this command.**")
            return

        # Ensure that there's at least one argument (the user ID)
        if len(command) < 1:
            await message.channel.send(
                self.not_enough_arguments.format(usage=self.usage)
            )
            return

        try:
            # Use the parser to extract the user ID
            user_id = parse_userid(command[0])
            user = await self.client.fetch_user(user_id)
        except ValueError as e:
            # Send the error message directly to the channel
            await message.channel.send(f"{str(e)}")
            return
        except discord.errors.NotFound:
            user = None

        # If the user is not found
        if user is None:
            await message.channel.send(
                self.invalid_user.format(user_id=user_id, usage=self.usage)
            )
            return

        # Extract the message content directly after the command, preserving formatting
        raw_content = message.content.split(None, 2)[-1]

        # Parse the message content to handle custom emojis and attachments
        parsed_content = parse_emotes(raw_content, self.client)
        parsed_content = parse_attachments(parsed_content)

        # Create the embed for the preceding message
        embed = discord.Embed(
            title="You have received a new message",
            description=f"From server: `{message.guild.name}`",
            color=discord.Color.blue()
        )

        # Prepare the list of files to send (if there are attachments)
        files = [await attachment.to_file() for attachment in message.attachments]

        # Send the embed and then the actual content to preserve formatting
        try:
            await user.send(embed=embed)

            if parsed_content.strip():
                await user.send(parsed_content)

            if files:
                await user.send(files=files)

            # React with a checkmark to the original message
            await message.add_reaction("✅")
        except discord.errors.HTTPException as e:
            await message.channel.send(f"Failed to send DM: {str(e)}")


# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__], 
    lambda member: inspect.isclass(member) and member.__module__ == __name__
)
