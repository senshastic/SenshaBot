from typing import Optional

import discord


class EmbedBuilder:
    """The Embed builder class, used to wrap the discord embed object to make common embeds easier to use"""

    def __init__(self, event: str) -> None:
        embeds = {
            "delete": discord.Embed(
                title="Deleted Message",
                description="A message was Deleted",
                color=0xFFFF00,
            ),
            "kick": discord.Embed(
                title="Kicked user", description="A user was Kicked", color=0xFF8000
            ),
            "mute": discord.Embed(
                title="Muted user", description="A user was Muted", color=0xFF8000
            ),
            "tempmute": discord.Embed(
                title="Temp Muted user",
                description="A user was Temp Muted",
                color=0xFF8000,
            ),
            "unmute": discord.Embed(
                title="Unmuted user", description="A user was Unmuted", color=0x00FF00
            ),
            "warn": discord.Embed(
                title="Warned user", description="A user was Warned", color=0xFF0000
            ),
            "warnlog": discord.Embed(
                title="Warnlog ran for user",
                description="A warnlog was ran",
                color=0xFF0000,
            ),
            "tempban": discord.Embed(
                title="Temp Banned user",
                description="A user was Temp Banned",
                color=0xFF0000,
            ),
            "ban": discord.Embed(
                title="Banned user", description="A user was Banned", color=0xFF0000
            ),
            "unban": discord.Embed(
                title="Unbanned user", description="A user was Unbanned", color=0x00FF00
            ),
            "banexpire": discord.Embed(
                title="Temp Ban Expired",
                description="A user's temp ban expired",
                color=0xFF8000,
            ),
            "muteexpire": discord.Embed(
                title="Temp Mute Expired",
                description="A user's temp mute expired",
                color=0x00FF00,
            ),
        }
        self.embed = embeds.get(event) or discord.Embed(title=event)

    async def add_field(
        self, name: str, value: str, inline: Optional[bool] = False
    ) -> None:
        """Add a field to the embed

        Args:
            name (str): The name for the field
            value (str): The contents of the field
            inline (bool, optional): Whether to use an inline field. Defaults to False.
        """
        self.embed.add_field(name=name, value=value, inline=inline)

    async def get_embed(self) -> discord.Embed:
        """Returns the embed object"""
        return self.embed
