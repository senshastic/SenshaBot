import asyncio
import time

from helpers.embed_builder import EmbedBuilder


async def check_punishments(client):
    while True:
        for guild in client.guilds:
            guild_id = str(guild.id)
            muted_role_id = int(client.storage.settings["guilds"][guild_id]["muted_role_id"])
            log_channel_id = int(client.storage.settings["guilds"][guild_id]["log_channel_id"])
            muted_role = guild.get_role(muted_role_id)
            log_channel = guild.get_channel(log_channel_id)

            # Handle muted users
            muted_users = client.storage.settings["guilds"][guild_id]["muted_users"]
            mutes_to_remove = []
            for user_info in muted_users.items():
                user_id = int(user_info[0])
                duration = int(user_info[1]["duration"])
                normal_duration = user_info[1]["normal_duration"]
                if -1 < duration < int(time.time()):
                    user = await guild.fetch_member(user_id)
                    if user is None:
                        continue
                    await user.remove_roles(muted_role, reason="Temp mute expired.")
                    mutes_to_remove.append(user_id)

                    embed_builder = EmbedBuilder(event="muteexpire")
                    await embed_builder.add_field(name="**Unmuted user**", value=f"`{user.name}`")
                    await embed_builder.add_field(name="**Mute duration**", value=f"`{normal_duration}`")
                    embed = await embed_builder.get_embed()
                    await log_channel.send(embed=embed)

            for user_id in mutes_to_remove:
                client.storage.settings["guilds"][guild_id]["muted_users"].pop(str(user_id))
            await client.storage.write_file_to_disk()

            # Handle banned users
            banned_users = client.storage.settings["guilds"][guild_id]["banned_users"]
            bans_to_remove = []
            for user_info in banned_users.items():
                user_id = int(user_info[0])
                duration = int(user_info[1]["duration"])
                normal_duration = user_info[1]["normal_duration"]
                if -1 < duration < int(time.time()):
                    user = await client.fetch_user(user_id)
                    if user is None:
                        continue
                    await guild.unban(user, reason="Temp ban expired")
                    bans_to_remove.append(user_id)

                    embed_builder = EmbedBuilder(event="banexpire")
                    await embed_builder.add_field(name="**Unbanned user**", value=f"`{user.name}`")
                    await embed_builder.add_field(name="**Ban duration**", value=f"`{normal_duration}`")
                    embed = await embed_builder.get_embed()
                    await log_channel.send(embed=embed)

            for user_id in bans_to_remove:
                client.storage.settings["guilds"][guild_id]["banned_users"].pop(str(user_id))
            await client.storage.write_file_to_disk()

            # Handle warns
            warned_users = client.storage.settings["guilds"][guild_id]["warned_users"]
            warns_to_clear = []
            for user_id, warn_data in warned_users.items():
                timestamps = warn_data["timestamp"]
                durations = warn_data["duration"]
                active_weights = warn_data["active_weight"]
                for i, (timestamp, duration, active_weight) in enumerate(zip(timestamps, durations, active_weights)):
                    if duration != -1 and timestamp + duration < time.time() and active_weight > 0:
                        warns_to_clear.append((user_id, i))

            for user_id, warn_index in warns_to_clear:
                user_warnings = client.storage.settings["guilds"][guild_id]["warned_users"][str(user_id)]
                user_warnings["active_weight"][warn_index] = 0

                user = await guild.fetch_member(int(user_id))
                if user is None:
                    continue

                embed_builder = EmbedBuilder(event="warnc")
                await embed_builder.add_field(name="**Executor**", value="`System`")
                await embed_builder.add_field(name="**Warn cleared for user**", value=f"`{user.name}`")
                await embed_builder.add_field(name="**Warn index**", value=f"`{warn_index}`")
                embed = await embed_builder.get_embed()
                await log_channel.send(embed=embed)

            await client.storage.write_file_to_disk()

        await asyncio.sleep(5)
