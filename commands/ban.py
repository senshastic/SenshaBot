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
                try:
                    # Use the parser to extract the user ID
                    user_id = parse_userid(command[0])
                    guild_id = str(message.guild.id)
                    
                    try:
                        # Try to unban the user by ID
                        await message.guild.unban(discord.Object(id=user_id), reason=f"Unbanned by {message.author.name}")
                        
                        # Remove from the banned list
                        self.storage.settings["guilds"][guild_id]["banned_users"].pop(str(user_id), None)
                        await self.storage.write_file_to_disk()

                        # Confirmation message
                        await message.channel.send(f"**Unbanned user with ID:** `{user_id}`.")

                        # Log the unban
                        log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            embed = discord.Embed(
                                title="User Unbanned",
                                description=f"**Executor:** {message.author.name}\n**Unbanned user:** {user_id}",
                                color=discord.Color.green()
                            )
                            await log_channel.send(embed=embed)
                    except discord.errors.NotFound:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                except ValueError as e:
                    await message.channel.send(str(e))
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
                try:
                    # Use the parser to extract the user ID
                    user_id = parse_userid(command[0])
                    duration = int(parse_duration(command[1]))

                    if is_valid_duration(duration):
                        guild_id = str(message.guild.id)
                        ban_duration = int(time.time()) + duration

                        # Extract reason for the ban
                        reason = " ".join(command[2:])

                        try:
                            # Ban the user
                            await message.guild.ban(discord.Object(id=user_id), reason=reason)

                            # Store ban information
                            self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)] = {
                                "duration": ban_duration,
                                "reason": reason,
                                "normal_duration": command[1],
                            }
                            await self.storage.write_file_to_disk()

                            # Send DM to the banned user
                            dm_subject = f"You have been banned from the {message.guild.name} server"
                            dm_args = [str(user_id), f"**{dm_subject}**", reason]
                            await self.dm_command.execute(message, args=dm_args)

                            # Confirmation message in the channel
                            await message.channel.send(f"**Banned user with ID:** `{user_id}`. **Reason:** `{reason}`.")

                            # Log the ban
                            log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                            log_channel = message.guild.get_channel(log_channel_id)
                            if log_channel:
                                embed = discord.Embed(
                                    title="User Banned",
                                    description=f"**Executor:** {message.author.name}\n**Banned user:** {user_id}\n**Reason:** {reason}",
                                    color=discord.Color.red()
                                )
                                await log_channel.send(embed=embed)

                        except discord.errors.NotFound:
                            await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                    else:
                        await message.channel.send(self.invalid_duration.format(usage=self.usage))
                except ValueError as e:
                    await message.channel.send(str(e))
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
                try:
                    # Use the parser to extract the user ID
                    user_id = parse_userid(command[0])
                    reason = " ".join(command[1:])
                    guild_id = str(message.guild.id)

                    try:
                        # Ban the user by ID even if they're not in the server
                        await message.guild.ban(discord.Object(id=user_id), reason=reason)

                        # Store ban information
                        self.storage.settings["guilds"][guild_id]["banned_users"][str(user_id)] = {
                            "duration": -1,  # No duration means a permanent ban
                            "reason": reason
                        }
                        await self.storage.write_file_to_disk()

                        # Confirmation message
                        await message.channel.send(f"**Banned user with ID:** `{user_id}`. **Reason:** `{reason}`.")

                    except discord.errors.NotFound:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))

                except ValueError as e:
                    await message.channel.send(str(e))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")



# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
