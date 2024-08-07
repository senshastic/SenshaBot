
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
                # Extract user ID
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if is_integer(command[0]):
                    user_id = int(command[0])
                    guild_id = str(message.guild.name)
                    try:
                        user = await self.client.fetch_user(user_id)
                    except discord.errors.NotFound:
                        user = None

                    # Extract subject and message
                    if len(command) >= 2:
                        if command[1].startswith("**") and command[1].endswith("**"):
                            subject = command[1][2:-2]
                            message_content = " ".join(command[2:])
                        else:
                            subject = f"**Message from the {guild_id} server**"
                            message_content = " ".join(command[1:])
                    else:
                        subject = "No Subject"
                        message_content = ""

                    if user is not None:
                        embed = discord.Embed(title=f"**{subject}**", description=message_content, color=discord.Color.blue())
                        try:
                            await user.send(embed=embed)

                            # Logging the DM command
                            embed_builder = EmbedBuilder(event="Private message was sent")
                            await embed_builder.add_field(name="**DM'd user**", value=f"`{user.name}`")
                            log_embed = await embed_builder.get_embed()

                            log_channel_id = int(self.storage.settings["guilds"][str(message.guild.id)]["log_channel_id"])
                            log_channel = message.guild.get_channel(log_channel_id)
                            if log_channel is not None:
                                await log_channel.send(embed=log_embed)
                        except discord.errors.HTTPException as e:
                            await message.channel.send(f"Failed to send DM: {str(e)}")
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")




# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
