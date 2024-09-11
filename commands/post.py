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

                    # Extract message
                    message_content = " ".join(command[1:])

                    if channel:
                        try:
                            # Configure allowed mentions to handle @everyone, @here, and user mentions
                            allowed_mentions = discord.AllowedMentions(everyone=True, users=True, roles=True)
                            
                            # Send the message with allowed mentions
                            await channel.send(message_content, allowed_mentions=allowed_mentions)
                            await message.channel.send(f"Message sent to {channel.mention}")
                            print(f"Message content to be sent: {message_content}")

                            # Logging the post command
                            embed_builder = EmbedBuilder(event="Message posted")
                            await embed_builder.add_field(name="**Channel**", value=f"`{channel.name}`")
                            await embed_builder.add_field(name="**Message**", value=f"`{message_content}`")
                            log_embed = await embed_builder.get_embed()

                            log_channel_id = int(self.storage.settings["guilds"][str(message.guild.id)]["log_channel_id"])
                            log_channel = message.guild.get_channel(log_channel_id)
                            if log_channel:
                                await log_channel.send(embed=log_embed)
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


# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
