import discord
from discord.ext import commands, tasks
import asyncio

RADIO_STREAM_URL = "https://www.radio.net/s/247continuous"

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
            await ctx.send("🔊 Бот уже в голосовом канале, запускаю радио…")
            ensure_radio_running.start()
            return

        voice_client = await channel.connect(reconnect=True)
        await ctx.send(f"🔊 Подключился к **{channel.name}** и запускаю радио!")
        ensure_radio_running.start()

    @tasks.loop(seconds=5)
    async def ensure_radio_running():
        """
        Бесконечный мониторинг проигрывателя:
        - если бот не подключён → подключиться
        - если поток остановился → перезапустить
        - если бот вылетел → переподключиться
        """
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
                'options': '-vn -loglevel panic'
            }
            source = discord.FFmpegPCMAudio(RADIO_STREAM_URL, **ffmpeg_options)
            voice_client.play(source)

        try:
            await voice_client.ws.ping()
        except:
            try:
                voice_client = await channel.connect(reconnect=True)
            except:
                pass

    @bot.command(name="leave")
    async def leave(ctx):
        """Отключение радио (если понадобится)"""
        global voice_client
        if ctx.voice_client:
            ensure_radio_running.stop()
            await ctx.voice_client.disconnect()
            voice_client = None
            await ctx.send("🛑 Радио остановлено и бот отключён.")
        else:
            await ctx.send("❌ Я и так не в голосовом канале.")
