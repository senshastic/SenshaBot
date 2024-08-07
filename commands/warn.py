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


import discord
import re
import time
from datetime import timedelta

class WarnCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "warn"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}warn <user id> [reason]"
        self.invalid_user = "There is no user with the user ID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to warn. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

        # Initialize the DMCommand class
        self.dm_command = DMCommand(client_instance)

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 1:
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if is_integer(command[0]):
                    if not ((len(command) >= 1) & is_integer(command[1])):
                        command = [command[0], 1] + command[1:]
                    guild_id = str(message.guild.id)
                    user_id = int(command[0])
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    weight = int(command[1])
                    if len(command) >= 3:
                        temp = [item for item in command if command.index(item) > 1]
                        reason = " ".join(temp)
                    else:
                        reason = "Warned"
                    if user is not None:
                        warned_users = self.storage.settings["guilds"][guild_id].get("warned_users", {})
                        if str(user_id) not in warned_users:
                            warned_users[str(user_id)] = {
                                "weight": [],
                                "active_weight": [],
                                "executor": [],
                                "clearer": [],
                                "reason": [],
                                "timestamp": [],
                                "duration": [],
                                "normal_duration": []
                            }
                        warned_users[str(user_id)]["weight"].append(weight)
                        warned_users[str(user_id)]["active_weight"].append(weight)
                        warned_users[str(user_id)]["executor"].append(f"{message.author.name}")
                        warned_users[str(user_id)]["clearer"].append("")
                        warned_users[str(user_id)]["reason"].append(f"{reason}")
                        warned_users[str(user_id)]["timestamp"].append(time.time())
                        warned_users[str(user_id)]["duration"].append(60*5)
                        warned_users[str(user_id)]["normal_duration"].append(-1)
                        self.storage.settings["guilds"][guild_id]["warned_users"] = warned_users
                        await self.storage.write_file_to_disk()

                        active_warns = sum(warned_users[str(user_id)]["active_weight"])

                        await message.channel.send(f"**Warned user:** `{user.name}`**. Reason:** `{reason}`**.** \n *Number of active warns: `{active_warns}`.*")
                        
                        # Determine the DM subject based on the weight
                        if weight > 0:
                            subject = f"You have been warned in the {message.guild.name} server"
                        else:
                            subject = f"You have received a rule clarification from the {message.guild.name} server"

                        # Send DM using DMCommand
                        dm_args = [str(user_id), f"**{subject}**", reason]
                        await self.dm_command.execute(message, args=dm_args)

                        # Takes punishment action 
                        

                        if active_warns == 2 and weight != 0:
                            temp_mute_command = timeoutCommand(self.client)
                            await temp_mute_command.execute(message, args=[str(user_id), "24h", "Accrued two warnings"])
                        elif active_warns >= 3 and weight != 0:
                            temp_ban_command = TempBanCommand(self.client)
                            await temp_ban_command.execute(message, args=[str(user_id), "24h", "Accrued three warnings"])
                        
                        log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                        log_channel = message.guild.get_channel(log_channel_id)
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")




class WarncCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "warnc"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}warnc <user id> [warn index]"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to unwarn. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 1:
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if is_integer(command[0]):
                    guild_id = str(message.guild.id)
                    user_id = int(command[0])
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None

                    if user is not None:
                        if str(user_id) in self.storage.settings["guilds"][guild_id]["warned_users"]:
                            user_warnings = self.storage.settings["guilds"][guild_id]["warned_users"][str(user_id)]
                            
                            if "clearer" not in user_warnings:
                                user_warnings["clearer"] = [None] * len(user_warnings["active_weight"])
                            
                            if len(command) >= 2 and is_integer(command[1]):
                                warn_index = int(command[1])
                                if 0 <= warn_index < len(user_warnings["active_weight"]):
                                    if user_warnings["active_weight"][warn_index] > 0:
                                        user_warnings["active_weight"][warn_index] = 0
                                        user_warnings["clearer"][warn_index] = f"{message.author.name}"
                                        await message.channel.send(f"**Warn** `{warn_index}` **cleared for user:** `{user.name}`**")
                                    else:
                                        await message.channel.send(f"Warn `{warn_index}` is already cleared for user: `{user.name}`")
                                else:
                                    await message.channel.send(f"Invalid warn index: {warn_index}")
                            else:
                                for i in range(len(user_warnings["active_weight"])):
                                    if user_warnings["active_weight"][i] > 0:
                                        user_warnings["active_weight"][i] = 0
                                        user_warnings["clearer"][i] = f"{message.author.name}"
                                await message.channel.send(f"**Cleared all warns for user:** `{user.name}`")

                            await self.storage.write_file_to_disk()
                            
                            embed_builder = EmbedBuilder(event="warnc")
                            await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                            await embed_builder.add_field(name="**Warn(s) cleared for user**", value=f"`{user.name}`")
                            if len(command) >= 2 and is_integer(command[1]):
                                await embed_builder.add_field(name="**Warn index**", value=f"`{warn_index}`")
                            else:
                                await embed_builder.add_field(name="**Action**", value="Cleared all warns")
                            embed = await embed_builder.get_embed()
                            log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                            log_channel = message.guild.get_channel(log_channel_id)
                            
                        else:
                            await message.channel.send(f"No warnings found for user: `{user.name}`")
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


class WarnLogCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "warnlog"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}warnlog <user id>"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to view warn logs. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 1:
                if re.match(r'<@\d{18}>', command[0]):
                    command[0] = command[0][2:-1]
                if is_integer(command[0]):
                    user_id = int(command[0])
                    guild_id = str(message.guild.id)

                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None

                    if user is not None:
                        warned_users = self.storage.settings["guilds"][guild_id]["warned_users"]
                        user_warnings = warned_users.get(str(user_id))

                        if user_warnings:
                            current_weight = sum(user_warnings["active_weight"])
                            total_weight = sum(user_warnings["weight"])
                            embed = discord.Embed(title=f"Warnlog for {user.name}", color=0xff0000)
                            embed.add_field(
                                name="Current number of warns",
                                value=f"*{current_weight}*",
                                inline=False
                            )
                            embed.add_field(
                                name="Total number of warns",
                                value=f"*{total_weight}*",
                                inline=False
                            )
                            for index, (weight, active_weight, reason, timestamp, executor, clearer) in enumerate(zip(user_warnings["weight"], user_warnings["active_weight"], user_warnings["reason"], user_warnings["timestamp"], user_warnings["executor"], user_warnings["clearer"]), 1):
                                if active_weight == 0:
                                    if not clearer:
                                        clearer = "expiry"
                                    field_name = f"#{index} ~~**On:** {datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M')} **by** {executor}~~ **cleared by** {clearer}"
                                    field_value = f"*Weight: {weight}*\n{reason}\n"
                                else:
                                    field_name = f"#{index} **On:** {datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M')} **by** {executor}"
                                    field_value = f"*Weight: {weight}*\n{reason}\n"
                                
                                embed.add_field(
                                    name=field_name,
                                    value=field_value,
                                    inline=False
                                )
                            await message.channel.send(embed=embed)
                        else:
                            await message.channel.send(f"**{user.name}** has no warnings.")
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

