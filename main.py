import discord
import os
from discord.ext import commands
from webservis import keep_alive

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Запущен {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Проверка успешна {round(bot.latency * 1000)}ms")

keep_alive()

bot.run(os.getenv("TOKEN"))
