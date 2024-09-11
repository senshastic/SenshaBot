
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
from helpers.misc_functions import (author_is_mod, is_integer,
                                    is_valid_duration, parse_duration)


from helpers.emoji_parser import parse_emotes

from helpers.userid_parser import parse_userid

class DMCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "dm"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}dm <user id> **subject** <message>"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to DM. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 1:
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

                if user is not None:
                    # Extract subject and message
                    if len(command) >= 2:
                        if command[1].startswith("**") and command[1].endswith("**"):
                            subject = command[1][2:-2]
                            message_content = " ".join(command[2:])
                        else:
                            subject = f"**Message from the {message.guild.name} server**"
                            message_content = " ".join(command[1:])
                    else:
                        subject = "No Subject"
                        message_content = ""

                    # Parse the message content to replace custom emojis
                    message_content = parse_emotes(message_content, self.client)

                    # Create and send the embed message
                    embed = discord.Embed(title=f"**{subject}**", description=message_content, color=discord.Color.blue())
                    try:
                        await user.send(embed=embed)

                        # React with a checkmark to the original message
                        await message.add_reaction("✅")
                    except discord.errors.HTTPException as e:
                        await message.channel.send(f"Failed to send DM: {str(e)}")
                else:
                    await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
