import discord
from discord.ext import commands
import requests
import os
from webservis import keep_alive

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
        nick_value = self.nick.value.strip()
        name_value = self.name.value.strip()
        ur_value = self.ur.value.lower().strip()

        params = {
            "application_id": WOT_API_KEY,
            "search": nick_value,
            "type": "startswith",
            "limit": 5
        }

        try:
            r = requests.get("https://api.worldoftanks.eu/wot/account/list/", params=params, timeout=10).json()
            print("account/list response:", r)  # отладка
        except Exception as e:
            await interaction.user.send(f"Ошибка запроса account/list: {e}")
            return

        if "data" not in r or not r["data"]:
            await interaction.user.send(f"Ошибка: игрок '{nick_value}' не найден! Ответ API: {r}")
            return
        account_id = None
        for acc_id, info in r["data"].items():
            print("Найден ник:", info.get("nickname"))  # отладка
            if info.get("nickname", "").upper() == nick_value.upper():
                account_id = acc_id
                break

        if not account_id:
            account_id = list(r["data"].keys())[0]
            print("Выбрали первый account_id:", account_id)

        try:
            r2 = requests.get("https://api.worldoftanks.eu/wot/account/info/", params={
                "application_id": WOT_API_KEY,
                "account_id": account_id,
                "fields": "clan_id,nickname"
            }, timeout=10).json()
            print("account/info response:", r2)
        except Exception as e:
            await interaction.user.send(f"Ошибка запроса account/info: {e}")
            return

        player_data = r2.get("data", {}).get(account_id, {})
        player_clan_id = player_data.get("clan_id", 0)
        player_nick = player_data.get("nickname", nick_value)

        if player_clan_id != int(CLAN_ID):
            await interaction.user.send(f"Ошибка: игрок '{player_nick}' не в клане! Ответ API: {player_data}")
        else:
            guild = interaction.guild
            member = guild.get_member(interaction.user.id)
            role_to_add = guild.get_role(ROLE_TO_ADD)
            role_to_remove = guild.get_role(ROLE_TO_REMOVE)
            if role_to_remove:
                await member.remove_roles(role_to_remove)
            if role_to_add:
                await member.add_roles(role_to_add)

            await interaction.user.send(f"Добро пожаловать в клан '{player_nick} ({name_value})'!")

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
