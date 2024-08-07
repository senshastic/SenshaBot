import inspect
import sys
import time
import json

import discord

from bot import ModerationBot
from commands.base import Command
from helpers.embed_builder import EmbedBuilder
from helpers.misc_functions import (
    author_is_mod,
    is_integer,
    is_valid_duration,
    parse_duration,
)

# Collects a list of classes in the file
classes = inspect.getmembers(
    sys.modules[__name__],
    lambda member: inspect.isclass(member) and member.__module__ == __name__,
)
