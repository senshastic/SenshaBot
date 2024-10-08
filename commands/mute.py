import inspect
import sys
import time
import json 
import re 

import discord

from bot import ModerationBot
from commands.base import Command
from commands.dm import DMCommand
from datetime import timedelta
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (
    author_is_mod,
    is_integer,
    is_valid_duration,
    parse_duration,
)


from helpers.userid_parser import parse_userid

# deprecated 
"""
class UnMuteCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "unmute"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}unmute <user id>"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to unmute. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) == 1:
                if re.match(r"<@\d{18}>", command[0]):
                    command[0] = command[0][2:-1]
                if is_integer(command[0]):
                    guild_id = str(message.guild.id)
                    user_id = int(command[0])
                    muted_role_id = int(
                        self.storage.settings["guilds"][guild_id]["muted_role_id"]
                    )
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    muted_role = message.guild.get_role(muted_role_id)
                    if user is not None:
                        # Remove the muted role from the user and remove them from the guilds muted users list
                        await user.remove_roles(
                            muted_role, reason=f"Unmuted by {message.author.name}"
                        )
                        self.storage.settings["guilds"][guild_id]["muted_users"].pop(
                            str(user_id)
                        )
                        await self.storage.write_file_to_disk()
                        # Message the channel
                        await message.channel.send(
                            f"**Unmuted user:** `{user.name}`**.**"
                        )

                        # Build the embed and message it to the log channel
                        embed_builder = EmbedBuilder(event="unmute")
                        await embed_builder.add_field(
                            name="**Executor**", value=f"`{message.author.name}`"
                        )
                        await embed_builder.add_field(
                            name="**Unmuted user**", value=f"`{user.name}`"
                        )
                        embed = await embed_builder.get_embed()
                        log_channel_id = int(
                            self.storage.settings["guilds"][guild_id]["log_channel_id"]
                        )
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            await log_channel.send(embed=embed)
                    else:
                        await message.channel.send(
                            self.invalid_user.format(user_id=user_id, usage=self.usage)
                        )
                else:
                    await message.channel.send(
                        self.not_a_user_id.format(user_id=command[0], usage=self.usage)
                    )
            else:
                await message.channel.send(
                    self.not_enough_arguments.format(usage=self.usage)
                )
        else:
            await message.channel.send(
                "**You must be a moderator to use this command.**"
            )


class MuteCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "mute"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}mute <user id> [reason]"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to mute. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 1:
                if re.match(r"<@\d{18}>", command[0]):
                    command[0] = command[0][2:-1]
                if is_integer(command[0]):
                    guild_id = str(message.guild.id)
                    user_id = int(command[0])
                    muted_role_id = int(
                        self.storage.settings["guilds"][guild_id]["muted_role_id"]
                    )
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    muted_role = message.guild.get_role(muted_role_id)
                    if len(command) >= 2:
                        # Collects everything after the first item in the command and uses it as a reason.
                        temp = [item for item in command if command.index(item) > 0]
                        reason = " ".join(temp)
                    else:
                        reason = f"Muted by {message.author.name}"
                    if user is not None:
                        # Add the muted role and store them in guilds muted users list. We use -1 as the duration to state that it lasts forever.
                        await user.add_roles(
                            muted_role, reason=f"Muted by {message.author.name}"
                        )
                        self.storage.settings["guilds"][guild_id]["muted_users"][
                            str(user_id)
                        ] = {}
                        self.storage.settings["guilds"][guild_id]["muted_users"][
                            str(user_id)
                        ]["duration"] = -1
                        self.storage.settings["guilds"][guild_id]["muted_users"][
                            str(user_id)
                        ]["reason"] = reason
                        self.storage.settings["guilds"][guild_id]["muted_users"][
                            str(user_id)
                        ]["normal_duration"] = -1
                        await self.storage.write_file_to_disk()
                        # Message the channel
                        await message.channel.send(
                            f"**Permanently muted user:** `{user.name}`**. Reason:** `{reason}`"
                        )

                        # Build the embed and message it to the log channel
                        embed_builder = EmbedBuilder(event="mute")
                        await embed_builder.add_field(
                            name="**Executor**", value=f"`{message.author.name}`"
                        )
                        await embed_builder.add_field(
                            name="**Muted user**", value=f"`{user.name}`"
                        )
                        await embed_builder.add_field(
                            name="**Reason**", value=f"`{reason}`"
                        )
                        embed = await embed_builder.get_embed()
                        log_channel_id = int(
                            self.storage.settings["guilds"][guild_id]["log_channel_id"]
                        )
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            await log_channel.send(embed=embed)

                    else:
                        await message.channel.send(
                            self.invalid_user.format(user_id=user_id, usage=self.usage)
                        )
                else:
                    await message.channel.send(
                        self.not_a_user_id.format(user_id=command[0], usage=self.usage)
                    )
            else:
                await message.channel.send(
                    self.not_enough_arguments.format(usage=self.usage)
                )
        else:
            await message.channel.send(
                "**You must be a moderator to use this command.**"
            )
"""

class timeoutCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "timeout"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}timeout <user id> <duration> [reason]"
        self.invalid_user = "There is no user with the user ID: {user_id}. {usage}"
        self.invalid_duration = "The provided format is invalid. The duration must be a string that looks like: 1w3d5h30m20s or a positive number in seconds. {usage}"
        self.not_enough_arguments = "You must provide a user to timeout. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

        # Initialize the DMCommand class
        self.dm_command = DMCommand(client_instance)

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 2:
                try:
                    # Use the parser to extract the user ID
                    user_id = parse_userid(command[0])
                    duration = int(parse_duration(command[1]))

                    if is_valid_duration(duration):
                        guild_id = str(message.guild.id)
                        mute_duration = int(time.time()) + duration
                        try:
                            user = await message.guild.fetch_member(user_id)
                        except discord.errors.NotFound:
                            user = None

                        # Handle reason for timeout
                        if len(command) >= 3:
                            reason = " ".join(command[2:])
                        else:
                            reason = f"Timeouted by {message.author.name}"

                        if user is not None:
                            # Apply the timeout and store users in guilds timeout list
                            await user.timeout(
                                timedelta(seconds=duration),
                                reason=reason,
                            )
                            self.storage.settings["guilds"][guild_id]["muted_users"][
                                str(user_id)
                            ] = {
                                "duration": mute_duration,
                                "reason": reason,
                                "normal_duration": command[1],
                            }
                            await self.storage.write_file_to_disk()

                            # Send DM to the timeouted user
                            dm_subject = f"You have been timeouted from the {message.guild.name} server for {command[1]}"
                            dm_message = reason
                            dm_args = [str(user_id), f"**{dm_subject}**", dm_message]
                            await self.dm_command.execute(message, args=dm_args)

                            # Message the channel
                            await message.channel.send(
                                f"**Timeouted user:** `{user.name}` **for:** `{command[1]}` **. Reason:** `{reason}`**.**"
                            )

                            # Log the timeout to the log channel
                            log_channel_id = int(
                                self.storage.settings["guilds"][guild_id]["log_channel_id"]
                            )
                            log_channel = message.guild.get_channel(log_channel_id)
                            if log_channel:
                                await log_channel.send(f"Timeout applied to {user.name} for {command[1]}.")

                        else:
                            await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                    else:
                        await message.channel.send(self.invalid_duration.format(usage=self.usage))

                except ValueError as e:
                    # Handle invalid user ID or mention
                    await message.channel.send(str(e))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
