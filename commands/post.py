import inspect
import sys
import time
import json 
import re 

import discord

from bot import ModerationBot
from commands.base import Command
from datetime import datetime
from commands.mute import timeoutCommand
from commands.ban import TempBanCommand
from commands.dm import DMCommand
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (author_is_mod, is_integer,
                                    is_valid_duration, parse_duration)

from helpers.emoji_parser import parse_emotes
from helpers.userid_parser import parse_userid
from helpers.attachment_parser import parse_attachments


class PostCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "post"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}post <channel id> <message>"
        self.invalid_channel = "There is no channel with the channel ID: {channel_id}. {usage}"
        self.not_enough_arguments = "You must provide a channel and a message to post. {usage}"
        self.not_a_channel_id = "{channel_id} is not a valid channel ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 2:
                # Extract channel ID
                if re.match(r'<#\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if is_integer(command[0]):
                    channel_id = int(command[0])
                    channel = self.client.get_channel(channel_id)

                    # Extract message content
                    message_content = " ".join(command[1:])

                    # Parse potential mentions in the message
                    message_content = await self.parse_mentions(message_content, message.guild)

                    # Parse the message content to replace custom emojis
                    message_content = parse_emotes(message_content, self.client)

                    # Parse the message content for attachments
                    message_content = parse_attachments(message_content)

                    if channel:
                        try:
                            # Configure allowed mentions to handle @everyone, @here, and user mentions
                            allowed_mentions = discord.AllowedMentions(everyone=True, users=True, roles=True)

                            # Send the message with allowed mentions
                            await channel.send(message_content, allowed_mentions=allowed_mentions)

                            # React with a checkmark to the command message
                            await message.add_reaction("✅")

                        except discord.errors.HTTPException as e:
                            await message.channel.send(f"Failed to send message: {str(e)}")
                    else:
                        await message.channel.send(self.invalid_channel.format(channel_id=channel_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_channel_id.format(channel_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")

    async def parse_mentions(self, message_content: str, guild: discord.Guild) -> str:
        """Parse and replace user mentions in the message content with actual mentions."""
        words = message_content.split()
        parsed_message = []
        for word in words:
            try:
                # Attempt to parse each word as a user mention or raw user ID
                user_id = parse_userid(word)
                user = guild.get_member(user_id)
                if user:
                    parsed_message.append(user.mention)
                else:
                    parsed_message.append(word)  # If not a valid mention, leave as is
            except ValueError:
                parsed_message.append(word)  # If parsing fails, leave as is

        return " ".join(parsed_message)



# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
