import discord
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Запущен {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Проверка успешна {round(bot.latency * 1000)}ms")

bot.run(os.getenv("TOKEN"))

