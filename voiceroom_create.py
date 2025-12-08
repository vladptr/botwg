import discord

TEMP_VC_CATEGORY_ID = 1446977211499417712
TRIGGER_VC_ID = 1447689737488826398

def setup_voice_handlers(bot: discord.Client):
    @bot.event
    async def on_voice_state_update(member, before, after):
        guild = member.guild

        if after.channel and after.channel.id == TRIGGER_VC_ID:
            category = guild.get_channel(TEMP_VC_CATEGORY_ID)
            if category is None:
                return
            new_vc = await guild.create_voice_channel(
                name=f"🎮 Соло {member.display_name}",
                category=category,
                reason="Temporary VC created for user"
            )
            await member.move_to(new_vc)

        if before.channel and before.channel.category_id == TEMP_VC_CATEGORY_ID:
            if before.channel.id != TRIGGER_VC_ID and len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="Temporary VC empty")
                except:
                    pass
