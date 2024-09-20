import inspect
import sys
import time
import json 
import re 
import os

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

import discord
from discord.ext import commands

from discord.ui import View, Button

import time
import re

from helpers.emoji_parser import parse_emotes

class EmojiChainWatcher(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "watchchain"
        self.client = client_instance
        self.emoji_chain = []
        self.chain_length = 5  # Define the chain length threshold
        self.bonk_emoji_name = "BC_bonk"  # The custom emoji name to use for reaction

    def is_emoji_only_message(self, message: discord.Message) -> bool:
        """Checks if the message contains only emojis."""
        # Return True if the message contains only emojis
        return all(word.startswith(":") and word.endswith(":") for word in message.content.split())

    def get_custom_emoji(self, name):
        """Fetch the bot's custom emoji by name."""
        for emoji in self.client.emojis:
            if emoji.name == name:
                return emoji
        return None  # Return None if the emoji is not found

    async def handle_message(self, message: discord.Message) -> None:
        """Handle each message to check if it is part of an emoji chain."""
        # Ignore messages from the bot itself
        if message.author == self.client.user:
            return

        # Check if the message contains only emojis
        if self.is_emoji_only_message(message):
            self.emoji_chain.append(message)

            # Only keep track of the last 5 messages in the chain
            if len(self.emoji_chain) > self.chain_length:
                self.emoji_chain.pop(0)
        else:
            # If a message breaks the chain and the chain is long enough
            if len(self.emoji_chain) >= self.chain_length:
                # React with the BC_bonk emoji
                bonk_emoji = self.get_custom_emoji(self.bonk_emoji_name)
                if bonk_emoji:
                    await message.add_reaction(bonk_emoji)

            # Reset the chain if broken
            self.emoji_chain.clear()

    async def execute(self, message: discord.Message, **kwargs) -> None:
        # This command doesn't respond directly, it's a background process for watching emoji chains.
        await self.handle_message(message)


# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
