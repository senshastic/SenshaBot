
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

from helpers.userid_parser import parse_userid

class DMChannelCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "dmchannel"
        self.client = client_instance
        self.storage = client_instance.storage  # Access to the storage system
        self.usage = f"Usage: {self.client.prefix}dmchannel <channel id or mention>"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):  # Only mods can set the DM channel
            if len(command) == 1:
                channel_id = command[0].strip("<#>")
                if channel_id.isdigit():
                    guild_id = str(message.guild.id)
                    channel = message.guild.get_channel(int(channel_id))

                    if channel:
                        # Set the DM channel in the settings
                        self.storage.settings["guilds"][guild_id]["dm_channel_id"] = int(channel_id)
                        await self.storage.write_file_to_disk()

                        await message.channel.send(f"DM channel has been set to {channel.mention}.")
                    else:
                        await message.channel.send(f"Channel with ID {channel_id} not found.")
                else:
                    await message.channel.send(self.usage)
            else:
                await message.channel.send(self.usage)
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
