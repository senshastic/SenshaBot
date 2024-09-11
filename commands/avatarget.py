
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

class AvatarTargetCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "avatarget"
        self.client = client_instance
        self.storage = client_instance.storage  # Ensure storage is initialized
        self.usage = f"Usage: {self.client.prefix}avatarget <user ID>"
        self.invalid_user = "There is no user with the user ID: {user_id}. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):  # Check if author is mod
            if len(command) >= 1:
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if re.match(r'&lt;@\d{18}&gt;', command[0]):
                    command[0] = command[0][5:-4]
                if is_integer(command[0]):
                    user_id = int(command[0])
                    try:
                        user = await self.client.fetch_user(user_id)
                        avatar_url = user.display_avatar.url  # Use display_avatar.url

                        # Send the avatar URL in the chat
                        await message.channel.send(f"Here is the avatar of user with ID `{user_id}`: {avatar_url}")
                    except discord.errors.NotFound:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(f"You must provide a user ID. {self.usage}")
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
