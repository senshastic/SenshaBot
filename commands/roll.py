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


import random

class RollCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "roll"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}roll"

    def get_custom_emoji(self, name):
        """Fetch the bot's custom emoji by name."""
        for emoji in self.client.emojis:
            if emoji.name == name:
                return str(emoji)  # Return the emoji object as a string
        return f":{name}:"  # Fallback in case the emoji is not found

    def roll_d20_normal(self):
        """Rolls a d20 with a normal distribution."""
        mean = 10.5  
        std_dev = 3   

        # Generate a normally distributed roll
        roll = random.gauss(mean, std_dev)

        # Round the result and clamp it between 1 and 20
        roll = max(1, min(20, round(roll)))
        return roll

    async def execute(self, message: discord.Message, **kwargs) -> None:
        roll = self.roll_d20_normal()  # Roll a d20 with normal distribution
        await message.channel.send(f"You rolled a {roll}!")

        # Get the emotes
        HaPoint = self.get_custom_emoji("HaPoint")
        fishap = self.get_custom_emoji("fishap")
        hapwiggle = self.get_custom_emoji("hapwiggle")
        pogcat = self.get_custom_emoji("pogcat")
        crown = self.get_custom_emoji("crown")
        pausecham = self.get_custom_emoji("pausecham")

        # Handle different outcomes based on the roll
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

