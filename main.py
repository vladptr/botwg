import discord
from discord.ext import commands
import requests
import os
from webservis import keep_alive

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())


WOT_API_KEY = "97d79abe59b0145f55a621ab80ad9a22"
CLAN_ID = "500242135"

TARGET_CHANNEL_ID = 1192780647429836818
ROLE_TO_ADD = 1192773043219615805
ROLE_TO_REMOVE = 1192773043219615805

class AuthModal(discord.ui.Modal, title="Авторизация в клане"):
    nick = discord.ui.TextInput(label="Никнейм в игре", placeholder="Введите никнейм")
    name = discord.ui.TextInput(label="Имя", placeholder="Ваше имя")
    ur = discord.ui.TextInput(label="Играешь укрепрайоны? (да/нет)", placeholder="да или нет")

    async def on_submit(self, interaction: discord.Interaction):
        nick_value = self.nick.value
        name_value = self.name.value
        ur_value = self.ur.value.lower()

        params = {
            "application_id": WOT_API_KEY,
            "search": nick_value,
            "type": "exact",
            "limit": 1
        }
        r = requests.get("https://api.worldoftanks.eu/wot/account/list/", params=params).json()
        if "data" not in r or not r["data"]:
            await interaction.user.send(f"Ошибка: игрок '{nick_value}' не найден!")
            return

        account_id = list(r["data"].keys())[0]

        r2 = requests.get("https://api.worldoftanks.eu/wot/account/info/", params={
            "application_id": WOT_API_KEY,
            "account_id": account_id,
            "fields": "clan_id"
        }).json()

        player_clan_id = r2["data"][account_id].get("clan_id", 0)

        if player_clan_id != int(CLAN_ID):
            await interaction.user.send(f"Ошибка: игрок '{nick_value}' не в клане!")
        else:
            guild = interaction.guild
            member = guild.get_member(interaction.user.id)
            role_to_add = guild.get_role(ROLE_TO_ADD)
            role_to_remove = guild.get_role(ROLE_TO_REMOVE)
            if role_to_remove:
                await member.remove_roles(role_to_remove)
            if role_to_add:
                await member.add_roles(role_to_add)

            await interaction.user.send(f"Добро пожаловать в клан '{nick_value} ({name_value})'!")

class AuthButton(discord.ui.View):
    @discord.ui.button(label="Авторизоваться", style=discord.ButtonStyle.green)
    async def auth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AuthModal())

@bot.command()
async def send_auth(ctx):
    if ctx.channel.id != TARGET_CHANNEL_ID:
        await ctx.send("Эта команда работает только в нужном канале.")
        return
    view = AuthButton()
    await ctx.send("Нажмите кнопку для авторизации в клане:", view=view)
    
keep_alive()
bot.run(os.getenv("TOKEN"))
