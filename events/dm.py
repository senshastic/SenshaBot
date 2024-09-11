import discord
from helpers.embed_builder import EmbedBuilder
from bot import ModerationBot
from events.base import EventHandler
import asyncio

from helpers.emoji_parser import parse_emotes


class DMHandler(EventHandler):
    def __init__(self, client_instance: ModerationBot) -> None:
        super().__init__(client_instance)
        self.client = client_instance
        self.event = "on_message"  # Trigger on receiving any message
        self.number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

    async def handle(self, message: discord.Message, *args, **kwargs) -> None:
        # Check if this is a DM and not a message from a bot
        if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
            user = message.author
            guilds_user_in = []

            # Find all guilds that the bot shares with the user
            for guild in self.client.guilds:
                member = guild.get_member(user.id)
                if member:
                    guilds_user_in.append(guild)

            # If the user is in only one guild, send the message directly to that guild's DM channel
            if len(guilds_user_in) == 1:
                await self.send_dm_to_guild(guilds_user_in[0], message)
                await message.add_reaction("✅")  # React with a checkmark when the DM is sent
            elif len(guilds_user_in) > 1:
                # Ask the user which server they want to send the message to
                embed = discord.Embed(
                    title="Select a Server",
                    description="To which server do you want to send this message? React with the corresponding number.",
                    color=discord.Color.blue()
                )
                for i, guild in enumerate(guilds_user_in):
                    embed.add_field(name=f"{self.number_emojis[i]} {guild.name}", value=f"ID: {guild.id}", inline=False)

                prompt_message = await user.send(embed=embed)

                # React with numbered emojis for selection and add a short delay between each reaction
                for i in range(len(guilds_user_in)):
                    await prompt_message.add_reaction(self.number_emojis[i])
                    await asyncio.sleep(0.5)  # Add a delay between each reaction to avoid hitting rate limits

                # Wait for the user's reaction to select the guild
                def check_reaction(reaction, reactor):
                    return reactor == user and str(reaction.emoji) in self.number_emojis[:len(guilds_user_in)]

                try:
                    reaction, _ = await self.client.wait_for('reaction_add', timeout=60.0, check=check_reaction)
                    selected_guild_index = self.number_emojis.index(str(reaction.emoji))
                    selected_guild = guilds_user_in[selected_guild_index]

                    # Send the message to the selected guild's DM channel
                    await self.send_dm_to_guild(selected_guild, message)
                    await message.add_reaction("✅")  # React with a checkmark when the DM is sent

                except asyncio.TimeoutError:
                    await user.send("You took too long to respond. Please try again.")

    async def send_dm_to_guild(self, guild: discord.Guild, message: discord.Message) -> None:
        user = message.author
        guild_id = str(guild.id)

        # Fetch the DM channel and log channel IDs from the guild settings
        dm_channel_id = self.client.storage.settings["guilds"][guild_id].get("dm_channel_id")
        log_channel_id = self.client.storage.settings["guilds"][guild_id].get("log_channel_id")

        # If no DM channel is set, fall back to the log channel
        channel = self.client.get_channel(dm_channel_id) if dm_channel_id else self.client.get_channel(log_channel_id)

        if channel:
            # Parse the message content for emotes before sending
            parsed_message_content = parse_emotes(message.content, self.client)

            # Create an embed to display the DM
            embed = discord.Embed(title="New DM Received", color=discord.Color.blue())
            embed.add_field(name="From", value=f"{user.mention} ({user.name}#{user.discriminator})", inline=False)
            embed.add_field(name="Message", value=parsed_message_content, inline=False)
            embed.set_footer(text=f"User ID: {user.id}")

            # Send the embed to the appropriate channel
            await channel.send(embed=embed)
        else:
            print(f"No valid DM or log channel set for guild {guild_id}.")