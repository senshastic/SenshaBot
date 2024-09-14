
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


class RequestableRoleCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "requestablerole"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}requestablerole <role ID>"
        self.not_a_role_id = "{role_id} is not a valid role ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        if await author_is_mod(message.author, self.storage):  # Ensure only mods can use this command
            if len(command) >= 1:
                try:
                    # Parse role ID using the new parser
                    role_id = parse_roleid(command[0])
                    guild_id = str(message.guild.id)

                    # Store the role in the requestable roles list
                    requestable_roles = self.storage.settings["guilds"].get(guild_id, {}).get("requestable_roles", [])
                    if str(role_id) not in requestable_roles:
                        requestable_roles.append(str(role_id))
                        self.storage.settings["guilds"][guild_id]["requestable_roles"] = requestable_roles
                        await self.storage.write_file_to_disk()

                        await message.channel.send(f"**Role with ID:** `{role_id}` is now requestable.")
                    else:
                        await message.channel.send(f"**Role with ID:** `{role_id}` is already requestable.")
                except ValueError as e:
                    await message.channel.send(str(e))
            else:
                await message.channel.send(f"You must provide a role ID. {self.usage}")
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


class RequestRoleCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "requestrole"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}requestrole <role ID>"
        self.invalid_role = "Role with ID: {role_id} is not requestable. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        if len(command) >= 1:
            try:
                # Parse the role ID using the role ID parser
                role_id = parse_roleid(command[0])
                guild_id = str(message.guild.id)

                # Fetch requestable roles from settings.json
                requestable_roles = self.storage.settings["guilds"].get(guild_id, {}).get("requestable_roles", [])

                if str(role_id) in requestable_roles:
                    role = message.guild.get_role(int(role_id))
                    if role:
                        await message.author.add_roles(role)
                        await message.channel.send(f"**You have been granted the role:** `{role.name}`.")
                    else:
                        await message.channel.send(f"**Role with ID:** `{role_id}` not found.")
                else:
                    await message.channel.send(self.invalid_role.format(role_id=role_id, usage=self.usage))
            except ValueError as e:
                await message.channel.send(str(e))
        else:
            await message.channel.send(f"You must provide a role ID. {self.usage}")



class RemoveRoleCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "removerole"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}removerole <role ID> [user ID]"
        self.invalid_role = "You do not have the role with ID: {role_id}. {usage}"
        self.not_a_moderator = "**You must be a moderator to remove roles from other users.**"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        
        if len(command) >= 1:
            try:
                # Parse the role ID using the role ID parser
                role_id = parse_roleid(command[-1])

                # Determine if a user ID is provided (for mods) or it’s the author themselves
                if len(command) == 2:
                    # Moderator trying to remove a role from another user
                    if await author_is_mod(message.author, self.storage):  
                        user_id = parse_userid(command[0])
                        user = message.guild.get_member(user_id)
                    else:
                        # Non-moderators cannot remove roles from other users
                        await message.channel.send(self.not_a_moderator)
                        return
                else:
                    # If no user ID is provided, remove the role from the command issuer
                    user = message.author

                # Fetch the role from the guild
                role = message.guild.get_role(int(role_id))

                if user and role and role in user.roles:
                    # Remove the role from the user
                    await user.remove_roles(role)
                    await message.channel.send(f"**{user.name} has removed the role:** `{role.name}`.")
                else:
                    await message.channel.send(self.invalid_role.format(role_id=role_id, usage=self.usage))
            except ValueError as e:
                await message.channel.send(str(e))
        else:
            await message.channel.send(f"You must provide a role ID. {self.usage}")

class GiveRoleCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "giverole"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}giverole <user ID> <role ID>"
        self.invalid_user = "User with ID: {user_id} not found. {usage}"
        self.invalid_role = "Role with ID: {role_id} not found. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        if await author_is_mod(message.author, self.storage):  # Check if the author is a moderator
            if len(command) >= 2:
                try:
                    # Parse user ID and role ID using the parsers
                    user_id = parse_userid(command[0])
                    role_id = parse_roleid(command[1])

                    # Fetch the user and role from the guild
                    guild = message.guild
                    user = guild.get_member(user_id)
                    role = guild.get_role(role_id)

                    if user:
                        if role:
                            # Add the role to the user
                            await user.add_roles(role)
                            await message.channel.send(f"**{user.name} has been granted the role:** `{role.name}`.")
                        else:
                            await message.channel.send(self.invalid_role.format(role_id=role_id, usage=self.usage))
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))

                except ValueError as e:
                    await message.channel.send(str(e))
            else:
                await message.channel.send(f"You must provide both a user ID and a role ID. {self.usage}")
        else:
            await message.channel.send("**You must be a moderator to use this command.**")

class NonRequestableRoleCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "nonrequestablerole"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}nonrequestablerole <role ID>"
        self.invalid_role = "Role with ID: {role_id} is not requestable. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args", [])
        if await author_is_mod(message.author, self.storage):  # Ensure only mods can use this command
            if len(command) >= 1:
                try:
                    # Parse the role ID using the role ID parser
                    role_id = parse_roleid(command[0])
                    guild_id = str(message.guild.id)

                    # Fetch requestable roles from settings.json
                    requestable_roles = self.storage.settings["guilds"].get(guild_id, {}).get("requestable_roles", [])

                    if str(role_id) in requestable_roles:
                        # Remove the role from the requestable roles list
                        requestable_roles.remove(str(role_id))
                        self.storage.settings["guilds"][guild_id]["requestable_roles"] = requestable_roles
                        await self.storage.write_file_to_disk()

                        await message.channel.send(f"**Role with ID:** `{role_id}` is no longer requestable.")
                    else:
                        await message.channel.send(self.invalid_role.format(role_id=role_id, usage=self.usage))
                except ValueError as e:
                    await message.channel.send(str(e))
            else:
                await message.channel.send(f"You must provide a role ID. {self.usage}")
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
