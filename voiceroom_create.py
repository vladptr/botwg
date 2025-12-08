import discord

TEMP_VC_CATEGORY_ID = 1446977211499417712
TRIGGER_VC_ID = 1446977494300229673

def setup_voice_handlers(bot: discord.Client):
    @bot.event
    async def on_voice_state_update(member, before, after):
        guild = member.guild

        if after.channel and after.channel.id == TRIGGER_VC_ID:
            category = guild.get_channel(TEMP_VC_CATEGORY_ID)
            new_vc = await guild.create_voice_channel(
                name=f"{member.display_name}'s room",
                category=category,
                reason="Temporary VC created for user"
            )
            await member.move_to(new_vc)

        if before.channel and before.channel.category_id == TEMP_VC_CATEGORY_ID:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="Temporary VC empty")
                except:
                    pass
