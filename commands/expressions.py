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
import json
from discord.ext import commands

from discord.ui import View, Button

import time
import re

from helpers.emoji_parser import parse_emotes

class ExasCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "exas"
        self.client = client_instance
        self.storage = client_instance.storage  # Access to the storage system
        self.usage = f"Usage: {self.client.prefix}exas <command name> <response>"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):  # Only mods can create commands
            if len(command) >= 2:
                # Strip surrounding quotes and prefix from command name
                cmd_name = command[0].strip('"')  # Do not store with the prefix
                if cmd_name.startswith(self.client.prefix):
                    cmd_name = cmd_name[len(self.client.prefix):]  # Remove the prefix

                # Rebuild the original message content to include newlines
                response = message.content.split(None, 2)[-1]  # Get everything after the command name

                # Parse the response to handle both custom emotes and bot-specific emotes
                response = parse_emotes(response, self.client)

                guild_id = str(message.guild.id)
                expressions_file = "expressions.json"  # Path to your expressions.json

                # Load existing expressions
                try:
                    with open(expressions_file, "r") as file:
                        expressions = json.load(file)
                except FileNotFoundError:
                    expressions = {}

                # Create the guild entry if it doesn't exist
                if guild_id not in expressions:
                    expressions[guild_id] = {"commands": {}}

                # Store or overwrite the command based on the trigger
                expressions[guild_id]["commands"][cmd_name] = {
                    "response": response,
                    "creator": message.author.name
                }

                # Save the updated expressions
                with open(expressions_file, "w") as file:
                    json.dump(expressions, file, indent=4)

                # Create an embed for the response
                embed = discord.Embed(title="Command Created/Updated", color=discord.Color.green())
                embed.add_field(name="Creator", value=message.author.name, inline=False)
                embed.add_field(name="Trigger", value=f"`{self.client.prefix}{cmd_name}`", inline=False)
                embed.add_field(name="Response", value=response, inline=False)
                embed.set_footer(text=f"Created/Updated in {message.guild.name}")

                # Send the embed
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(self.usage)
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


class ExaDeleteCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "exadelete"
        self.client = client_instance
        self.storage = client_instance.storage  # Access to the storage system
        self.usage = f"Usage: {self.client.prefix}exadelete <command name>"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):  # Only mods can delete commands
            if len(command) == 1:
                cmd_name = command[0].strip('"')

                guild_id = str(message.guild.id)
                expressions_file = "expressions.json"

                # Load existing expressions
                try:
                    with open(expressions_file, "r") as file:
                        expressions = json.load(file)
                except FileNotFoundError:
                    await message.channel.send("No commands found to delete.")
                    return

                # Check if the command with the given trigger exists
                if guild_id in expressions and cmd_name in expressions[guild_id]["commands"]:
                    del expressions[guild_id]["commands"][cmd_name]

                    # Save the updated expressions
                    with open(expressions_file, "w") as file:
                        json.dump(expressions, file, indent=4)

                    await message.channel.send(f"Command `{cmd_name}` has been deleted.")
                else:
                    await message.channel.send(f"Command `{cmd_name}` not found.")
            else:
                await message.channel.send(self.usage)
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


class ExaModifyCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "examodify"
        self.client = client_instance
        self.storage = client_instance.storage  # Access to the storage system
        self.usage = f"Usage: {self.client.prefix}examodify <command name> <new response>"

    async def execute(self, message: discord.Message, **kwargs) -> None:
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):  # Only mods can modify commands
            if len(command) >= 2:
                cmd_name = command[0].strip('"')

                # Preserve newlines by taking the entire message content after the command name
                new_response = message.content.split(None, 2)[-1]

                guild_id = str(message.guild.id)
                expressions_file = "expressions.json"

                # Load existing expressions
                try:
                    with open(expressions_file, "r") as file:
                        expressions = json.load(file)
                except FileNotFoundError:
                    await message.channel.send("No commands found to modify.")
                    return

                # Check if the command with the given trigger exists
                if guild_id in expressions and cmd_name in expressions[guild_id]["commands"]:
                    expressions[guild_id]["commands"][cmd_name]["response"] = new_response

                    # Save the updated expressions
                    with open(expressions_file, "w") as file:
                        json.dump(expressions, file, indent=4)

                    await message.channel.send(f"Command `{cmd_name}` has been modified with new response: `{new_response}`.")
                else:
                    await message.channel.send(f"Command `{cmd_name}` not found.")
            else:
                await message.channel.send(self.usage)
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


class ExaListCommand(Command):
    def __init__(self, client_instance: ModerationBot) -> None:
        self.cmd = "exalist"
        self.client = client_instance
        self.storage = client_instance.storage  # Access to the storage system

    async def execute(self, message: discord.Message, **kwargs) -> None:
        guild_id = str(message.guild.id)
        expressions_file = "expressions.json"

        # Load existing expressions
        try:
            with open(expressions_file, "r") as file:
                expressions = json.load(file)
        except FileNotFoundError:
            await message.channel.send("No commands found.")
            return

        # Check if the guild has commands
        if guild_id in expressions and expressions[guild_id]["commands"]:
            commands = expressions[guild_id]["commands"]
            command_list = [(cmd_name, cmd_data["creator"]) for cmd_name, cmd_data in commands.items()]

            # Divide the command list into pages of 10 commands each
            page_size = 10
            pages = [command_list[i:i + page_size] for i in range(0, len(command_list), page_size)]

            # Function to create the embed for a specific page
            def create_embed(page_index):
                embed = discord.Embed(title=f"Custom Commands (Page {page_index + 1}/{len(pages)})", color=discord.Color.blue())
                for cmd_name, creator in pages[page_index]:
                    embed.add_field(
                        name=f"Command `{cmd_name}`",
                        value=f"Created by: {creator}",
                        inline=False
                    )
                embed.set_footer(text=f"Page {page_index + 1} of {len(pages)}")
                return embed

            # Start on page 0
            current_page = 0
            embed = create_embed(current_page)

            # Create a button view for pagination
            class PaginationView(View):
                def __init__(self):
                    super().__init__(timeout=60)

                @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, disabled=True)
                async def previous_button(self, interaction: discord.Interaction, button: Button):
                    nonlocal current_page
                    if current_page > 0:
                        current_page -= 1
                        embed = create_embed(current_page)
                        if current_page == 0:
                            self.previous_button.disabled = True
                        self.next_button.disabled = False
                        await interaction.response.edit_message(embed=embed, view=self)

                @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, disabled=(len(pages) <= 1))
                async def next_button(self, interaction: discord.Interaction, button: Button):
                    nonlocal current_page
                    if current_page < len(pages) - 1:
                        current_page += 1
                        embed = create_embed(current_page)
                        if current_page == len(pages) - 1:
                            self.next_button.disabled = True
                        self.previous_button.disabled = False
                        await interaction.response.edit_message(embed=embed, view=self)

            view = PaginationView()
            await message.channel.send(embed=embed, view=view)
        else:
            await message.channel.send("No custom commands found for this server.")

# Collects a list of classes in the file
classes = inspect.getmembers(sys.modules[__name__], lambda member: inspect.isclass(member) and member.__module__ == __name__)
