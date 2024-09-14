import random
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

from helpers.emoji_parser import parse_emotes


class RollCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "roll"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}roll"
        self.roll_counter = 0  # Counter to track the number of rolls

    def get_custom_emoji(self, name):
        """Fetch the bot's custom emoji by name."""
        for emoji in self.client.emojis:
            if emoji.name == name:
                return str(emoji) 
        return f":{name}:"  # Fallback in case the emoji is not found

    def get_forced_roll(self):
        """Force a roll of 1 or 20 based on a condition."""
        # Alternate between forcing 1 or 20
        return 1 if self.roll_counter % 2 == 0 else 20

    async def execute(self, message: discord.Message, **kwargs) -> None:
        self.roll_counter += 1  # Increment the roll counter

        # Every 10th roll, force a 1 or 20
        if self.roll_counter % 10 == 0:
            roll = self.get_forced_roll()
        else:
            roll = random.randint(1, 20)  # Normal random 

        await message.channel.send(f"You rolled a {roll}!")

        # Get the emotes
        HaPoint = self.get_custom_emoji("HaPoint")
        fishap = self.get_custom_emoji("fishap")
        hapwiggle = self.get_custom_emoji("hapwiggle")
        pogcat = self.get_custom_emoji("pogcat")
        crown = self.get_custom_emoji("crown")
        pausecham = self.get_custom_emoji("pausecham")

        # different outcomes based on the roll
        if roll == 1:
            response = f"{HaPoint} you rolled a 1, critical fail!"
        elif 2 <= roll <= 10:
            response = f"{fishap} better luck next time, probably?"
        elif 11 <= roll <= 14:
            response = f"{pausecham} this one could go either way. It ain't bad but you can do better... Right?"
        elif 15 <= roll <= 19:
            response = f"{hapwiggle} not too bad! Probably passed that ability check!"
        elif roll == 20:
            response = f"{pogcat} Critical success! You dropped this: {crown}"

        # Send the final response
        await message.channel.send(response)

# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)

