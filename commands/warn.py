import inspect
import sys
import time
import json 

import discord

from bot import ModerationBot
from commands.base import Command
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (author_is_mod, is_integer,
                                    is_valid_duration, parse_duration)


class WarnCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "warn"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}warn <user id> [reason]"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to warn. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 1:
                if is_integer(command[0]):
                    if not ((len(command) >= 1) & is_integer(command[1])):
                        command = [command[0], 1] + command[1:]
                    guild_id = str(message.guild.id)
                    user_id = int(command[0])
                    # warned_role_id = int(self.storage.settings["guilds"][guild_id]["warned_role_id"])
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    # warned_role = message.guild.get_role(warned_role_id)
                    weight = int(command[1])
                    if len(command) >= 3:
                        # Collects everything after the first 2 items in the command and uses it as a reason.
                        temp = [item for item in command if command.index(item) > 1]
                        reason = " ".join(temp)
                    else:
                        reason = "Warned"  # f"Warned by {message.author.name}"
                    if user is not None:
                        # Add the warned role and store them in guilds warned users list. We use -1 as the duration to state that it lasts forever.
                        # await user.add_roles(warned_role, reason="Warned")
                        if str(user_id) not in self.storage.settings["guilds"][guild_id]["warned_users"]:
                            self.storage.settings["guilds"][guild_id]["warned_users"][str(user_id)] = {
                                "weight": [],
                                "reason": [],
                                "duration": [],
                                "normal_duration": []
                            }
                        self.storage.settings["guilds"][guild_id]["warned_users"][str(user_id)]["weight"].append(weight)
                        self.storage.settings["guilds"][guild_id]["warned_users"][str(user_id)]["reason"].append(f"{message.author.name}: {reason}")
                        self.storage.settings["guilds"][guild_id]["warned_users"][str(user_id)]["duration"].append(-1)
                        self.storage.settings["guilds"][guild_id]["warned_users"][str(user_id)]["normal_duration"].append(-1)
                        await self.storage.write_file_to_disk()
                        # Message the channel
                        await message.channel.send(f"**Warned user:** `{user.name}`**. Reason:** `{reason}`")
                        
                        # Build the embed and message it to the log channel
                        embed_builder = EmbedBuilder(event="warn")
                        await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                        await embed_builder.add_field(name="**Warned user**", value=f"`{user.name}`")
                        await embed_builder.add_field(name="**Reason**", value=f"`{reason}`")
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


# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)

