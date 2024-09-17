
import inspect
import sys
import time
import json 
import re 

import discord

from bot import ModerationBot
from commands.base import Command
from datetime import datetime
from datetime import timedelta
from commands.mute import timeoutCommand
from commands.ban import TempBanCommand
from commands.dm import DMCommand
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (author_is_mod, is_integer,
                                    is_valid_duration, parse_duration)


from helpers.userid_parser import parse_userid

from helpers.roleid_parser import parse_roleid


class RenameCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "rename"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}rename <user ID or mention> <new nickname>"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        if await author_is_mod(message.author, self.storage):  # Ensure only mods can use this command
            if len(command) >= 2:
                try:
                    # Parse the user ID using the user ID parser
                    user_id = parse_userid(command[0])
                    new_nickname = " ".join(command[1:])  # Get the new nickname from the rest of the arguments

                    # Fetch the user by ID
                    guild = message.guild
                    member = guild.get_member(user_id)
                    if member:
                        # Change the user's nickname
                        await member.edit(nick=new_nickname)
                        await message.channel.send(f"**{member.name}'s** nickname has been changed to **{new_nickname}**.")
                    else:
                        await message.channel.send(f"Could not find a member with the ID `{user_id}`.")
                except ValueError as e:
                    await message.channel.send(f"Invalid user ID or mention: {str(e)}")
            else:
                await message.channel.send(f"You must provide a user ID and a new nickname. {self.usage}")
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
