import bleach
import inspect
import sys
import discord
import re 

from bot import ModerationBot
from helpers.embed_builder import EmbedBuilder
from events.base import EventHandler
from helpers.misc_functions import author_is_mod

import json


class MessageEvent(EventHandler):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.client = client_instance
        self.storage = client_instance.storage
        self.event = "on_message"
        self.chain_length = 5  # Define the minimum length of the chain
        self.emoji_chain_file = "emoji_chain.json"  # JSON file to store emoji chains

        # Initialize the emoji chain file if it doesn't exist
        try:
            with open(self.emoji_chain_file, "r") as file:
                self.emoji_chains = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.emoji_chains = {}
            with open(self.emoji_chain_file, "w") as file:
                json.dump(self.emoji_chains, file)

    def save_emoji_chains(self) -> None:
        """Save the current emoji chains to the JSON file."""
        with open(self.emoji_chain_file, "w") as file:
            json.dump(self.emoji_chains, file, indent=4)

    def is_emoji_only_message(self, message: discord.Message) -> bool:
        """Check if the message contains only Discord-style emotes."""
        emote_pattern = r"(<a?:\w+:\d+>)"
        words = message.content.strip().split()

        # Return True only if all parts of the message match the emote pattern
        return all(re.fullmatch(emote_pattern, word) for word in words)

    def initialize_chain_for_channel(self, guild_id: str, channel_id: str) -> None:
        """Initialize the emoji chain for a given guild and channel if not already initialized."""
        if guild_id not in self.emoji_chains:
            self.emoji_chains[guild_id] = {}
        if channel_id not in self.emoji_chains[guild_id]:
            self.emoji_chains[guild_id][channel_id] = []

    def get_custom_emoji(self, name):
        """Fetch the bot's custom emoji by name."""
        for emoji in self.client.emojis:
            if emoji.name == name:
                return str(emoji)
        return f":{name}:"

    async def handle(self, message: discord.Message, *args, **kwargs) -> None:
        user = message.author
        if user.bot or not message.content:
            return

        # Extract the guild and channel ID
        guild_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        # Initialize the emoji chain for this guild and channel
        self.initialize_chain_for_channel(guild_id, channel_id)

        # Emoji chain detection logic
        if self.is_emoji_only_message(message):
            # Append the message to the chain
            self.emoji_chains[guild_id][channel_id].append(message.content)
            # Save the updated emoji chains to file
            self.save_emoji_chains()

        else:
            # If a message breaks the chain and the chain is long enough
            if len(self.emoji_chains[guild_id][channel_id]) >= self.chain_length:
                # React with the custom `:BC_bonk:` emote
                BC_bonk = self.get_custom_emoji("BC_bonk")
                await message.add_reaction(BC_bonk)

            # Reset the emoji chain for this channel
            self.emoji_chains[guild_id][channel_id] = []
            self.save_emoji_chains()

        # Check if the bot is mentioned
        if self.client.user.id in [mention.id for mention in message.mentions]:
            await message.reply("No u", mention_author=False)
            return

        # Clean the message content
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
                command_data = expressions[guild_id]["commands"][cmd]

                # Check if the command is mod-only and if the user is a mod
                if command_data.get("mod_only", False):  # Check if mod_only is True
                    if not await author_is_mod(user, self.storage):
                        await message.channel.send("**You must be a moderator to use this command.**")
                        return

                response = command_data["response"]

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


# deprecated log function
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
