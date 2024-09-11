import bleach
import inspect
import sys

import discord

from bot import ModerationBot
from helpers.embed_builder import EmbedBuilder
from events.base import EventHandler

import json 

class MessageEvent(EventHandler):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.client = client_instance
        self.event = "on_message"

    async def handle(self, message: discord.Message, *args, **kwargs) -> None:
        user = message.author
        if user.bot or not message.content:
            return

        # Check if the bot is mentioned
        if self.client.user.id in [mention.id for mention in message.mentions]:
            await message.reply("No u", mention_author=False)
            return

        message.content = bleach.clean(message.content)
        command = message.content.split()
        cmd = command.pop(0)

        if cmd.startswith(self.client.prefix):
            # Remove the prefix before searching in the expressions.json
            cmd = cmd[len(self.client.prefix):]

            guild_id = str(message.guild.id)
            expressions_file = "expressions.json"

            # Load custom commands from expressions.json
            try:
                with open(expressions_file, "r") as file:
                    expressions = json.load(file)
            except FileNotFoundError:
                expressions = {}

            # Check if the command exists in custom expressions
            if guild_id in expressions and cmd in expressions[guild_id]["commands"]:
                response = expressions[guild_id]["commands"][cmd]["response"]

                # Check if the response contains %target% and if the user provided a mention
                if "%target%" in response:
                    if message.mentions:  # If a user is mentioned, use the mention
                        target_mention = message.mentions[0].mention
                        response = response.replace("%target%", target_mention)
                    else:  # If no user is mentioned, remove %target%
                        response = response.replace("%target%", "")

                # Delete the user's message
                await message.delete()

                # Send the response
                await message.channel.send(response)
                return

            # Handle built-in commands
            command_handler = self.client.registry.get_command(cmd)
            if command_handler is not None:
                await command_handler(self.client).execute(
                    message,
                    command=cmd,
                    args=command,
                    storage=self.client.storage,
                    instance=self.client,
                )
            else:
                # Fetch log channel for unknown commands
                log_channel_id = int(self.client.storage.settings["guilds"][guild_id]["log_channel_id"])
                log_channel = message.guild.get_channel(log_channel_id)

                message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"

                if log_channel:
                    await log_channel.send(
                        f"**Unknown command:** `{cmd}` by {message.author.name}.\n"
                        f"[Jump to message]({message_link})"
                    )
                else:
                    await message.channel.send(f"**Unknown command:** `{cmd}`")


# dep
"""
class MessageDeleteEvent(EventHandler):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.client = client_instance
        self.event = "on_message_delete"

    async def handle(self, message: discord.Message, *args, **kwargs) -> None:
        # Ignore deletes of bot messages or messages from ourselves
        if message.author == self.client.user or message.author.bot:
            return
        # Build an embed that will log the deleted message
        embed_builder = EmbedBuilder(event="delete")
        await embed_builder.add_field(
            name="**Channel**", value=f"`#{message.channel.name}`"
        )
        await embed_builder.add_field(
            name="**Author**", value=f"`{message.author.name}`"
        )
        await embed_builder.add_field(name="**Message**", value=f"`{message.content}`")
        await embed_builder.add_field(
            name="**Created at**", value=f"`{message.created_at}`"
        )
        embed = await embed_builder.get_embed()

        # Message the log channel the embed of the deleted message
        guild_id = str(message.guild.id)
        log_channel_id = int(
            self.client.storage.settings["guilds"][guild_id]["log_channel_id"]
        )
        log_channel = discord.utils.get(message.guild.text_channels, id=log_channel_id)
        if log_channel is not None:
            await log_channel.send(embed=embed)
        else:
            print("No log channel found with that ID")
"""

# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
