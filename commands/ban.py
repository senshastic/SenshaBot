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


class UnBanCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "unban"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}unban <user ID>"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to unban. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) == 1:
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if re.match(r'&lt;@\d{18}&gt;', command[0]):
                      command[0] = command[0][5:-4]
                if is_integer(command[0]):
                    user_id = int(command[0])
                    guild_id = str(message.guild.id)
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    if user is not None:
                        # Unban the user and remove them from the guilds banned users list
                        await message.guild.unban(user, reason=f"Unbanned by {message.author.name}")
                        self.storage.settings["guilds"][guild_id]["banned_users"].pop(str(user_id))
                        await self.storage.write_file_to_disk()
                        # Message the channel
                        await message.channel.send(f"**Unbanned user:** `{user.name}`**.**")
                        
                        # Build the embed and message it to the log channel
                        embed_builder = EmbedBuilder(event="unban")
                        await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                        await embed_builder.add_field(name="**Unbanned user**", value=f"`{user.name}`")
                        embed = await embed_builder.get_embed()
                        log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            await log_channel.send(embed=embed)
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")
    

class TempBanCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "ban"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}ban <user ID> <duration> <reason>"
        self.invalid_user = "There is no user with the user ID: {user_id}. {usage}"
        self.invalid_duration = "The provided format is invalid. The duration must be a string that looks like: 1w3d5h30m20s or a positive number in seconds. {usage}"
        self.not_enough_arguments = "You must provide a user to ban. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

        # Initialize the DMCommand class
        self.dm_command = DMCommand(client_instance)

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 3:
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if re.match(r'&lt;@\d{18}&gt;', command[0]):
                      command[0] = command[0][5:-4]
                if is_integer(command[0]):
                    user_id = int(command[0])
                    duration = int(parse_duration(command[1]))
                    if is_valid_duration(duration):
                        guild_id = str(message.guild.id)
                        ban_duration = int(time.time()) + duration
                        try:
                            user = await message.guild.fetch_member(user_id)
                        except discord.errors.NotFound or discord.errors.HTTPException:
                            user = None
                        # Collects everything after the first two items in the command and uses it as a reason.
                        temp = [item for item in command if command.index(item) > 1]
                        reason = " ".join(temp)
                        if user is not None:

                            # Send DM to the banned user
                            dm_subject = f"You have been banned from the {message.guild.name} server"
                            dm_message = reason
                            dm_args = [str(user_id), f"**{dm_subject}**", dm_message]
                            await self.dm_command.execute(message, args=dm_args)

                            # Add the banned role and store them in guilds banned users list. We use -1 as the duration to state that it lasts forever.
                            await message.guild.ban(user, reason=reason)
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)] = {}
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)]["duration"] = ban_duration
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)]["reason"] = reason
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)]["normal_duration"] = command[1]
                            await self.storage.write_file_to_disk()
                            # Message the channel
                            await message.channel.send(f"**Banned user:** `{user.name}`. Reason:** `{reason}`.**")

                            log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                            log_channel = message.guild.get_channel(log_channel_id)
                        else:
                            await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                    else:
                        await message.channel.send(self.invalid_duration.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")



class PreBanCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "preban"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}preban <user ID> <reason>"
        self.invalid_user = "There is no user with the user ID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to ban. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 2:
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if re.match(r'&lt;@\d{18}&gt;', command[0]):
                    command[0] = command[0][5:-4]
                if is_integer(command[0]):
                    user_id = int(command[0])
                    guild_id = str(message.guild.id)

                    # Collect everything after the user ID as the reason.
                    reason = " ".join(command[1:])
                    try:
                        # Attempt to ban the user by ID even if they're not in the server
                        await message.guild.ban(discord.Object(id=user_id), reason=reason)
                        
                        # Store ban info
                        self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)] = {
                            "duration": -1,  # No duration means a permanent ban
                            "reason": reason
                        }
                        await self.storage.write_file_to_disk()
                        
                        # Confirmation message
                        await message.channel.send(f"**Banned user with ID:** `{user_id}`. **Reason:** `{reason}`.")
                    except discord.errors.NotFound:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")



# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
