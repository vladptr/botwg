import discord
from discord.ext import commands, tasks

RADIO_STREAM_URL = "https://live.wostreaming.net/direct/ppm-jazz24aac-ibc1"

voice_client: discord.VoiceClient | None = None
current_channel_id = None

def setup_radio(bot: commands.Bot):

    @bot.command(name="join")
    async def join(ctx):
        global voice_client, current_channel_id

        if not ctx.author.voice:
            await ctx.send("❌ Ты должен быть в голосовом канале!")
            return

        channel = ctx.author.voice.channel
        current_channel_id = channel.id

        if ctx.voice_client:
            voice_client = ctx.voice_client
            await ctx.send("🔊 Уже в голосовом канале, запускаю радио…")
            if not ensure_radio_running.is_running():
                ensure_radio_running.start()
            return

        voice_client = await channel.connect(reconnect=True)
        await ctx.send(f"🔊 Подключился к **{channel.name}** и запускаю радио!")
        ensure_radio_running.start()

    @tasks.loop(seconds=5)
    async def ensure_radio_running():
        global voice_client, current_channel_id

        if current_channel_id is None:
            return

        guild = bot.guilds[0]
        channel = guild.get_channel(current_channel_id)

        if voice_client is None or not voice_client.is_connected():
            try:
                voice_client = await channel.connect(reconnect=True)
            except:
                return

        if not voice_client.is_playing():
            ffmpeg_options = {
                "before_options": (
                    "-reconnect 1 "
                    "-reconnect_streamed 1 "
                    "-reconnect_delay_max 5 "
                    "-user_agent Mozilla/5.0"
                ),
                "options": "-vn"
            }

            source = discord.FFmpegPCMAudio(
                RADIO_STREAM_URL,
                **ffmpeg_options
            )

            voice_client.play(
                source,
                after=lambda e: print(f"[RADIO ERROR] {e}") if e else None
            )

    @bot.command(name="leave")
    async def leave(ctx):
        global voice_client

        if ctx.voice_client:
            ensure_radio_running.stop()
            await ctx.voice_client.disconnect()
            voice_client = None
            await ctx.send("🛑 Радио остановлено.")
        else:
            await ctx.send("❌ Я не в голосовом канале.")
