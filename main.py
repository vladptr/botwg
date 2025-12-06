import discord
from discord.ext import commands
import requests
import os
import asyncio
from webservis import keep_alive

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

WOT_API_KEY = "97d79abe59b0145f55a621ab80ad9a22"
CLAN_ID = 500348333
GUILD_ID = 1444626896422965411

TARGET_CHANNEL_ID = 1446969492830818508
ROLE_TO_ADD = 1444707586946633851
ROLE_TO_REMOVE = 1444707587961524389

class AuthModal(discord.ui.Modal, title="Авторизация в клане"):
    nick = discord.ui.TextInput(label="Никнейм в игре", placeholder="Введите никнейм")
    name = discord.ui.TextInput(label="Имя", placeholder="Ваше имя")
    ur = discord.ui.TextInput(label="Играешь укрепрайоны? (да/нет)", placeholder="да или нет")

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        nick_value = self.nick.value.strip()
        name_value = self.name.value.strip()

        try:
            r = requests.get(
                "https://api.worldoftanks.eu/wot/account/list/",
                params={
                    "application_id": WOT_API_KEY,
                    "search": nick_value,
                    "type": "exact",
                    "limit": 1
                },
                timeout=10
            ).json()
        except Exception as e:
            await interaction.followup.send(f"Ошибка запроса account/list: {e}", ephemeral=True)
            return

        data = r.get("data", [])
        account_id = None

        if isinstance(data, dict) and data:
            account_id = list(data.keys())[0]
        elif isinstance(data, list) and data:
            account_id = data[0].get("account_id")

        if not account_id:
            await interaction.followup.send(f"Игрок '{nick_value}' не найден!", ephemeral=True)
            return

        try:
            r2 = requests.get(
                "https://api.worldoftanks.eu/wot/account/info/",
                params={
                    "application_id": WOT_API_KEY,
                    "account_id": account_id,
                    "fields": "clan_id,nickname"
                },
                timeout=10
            ).json()
        except Exception as e:
            await interaction.followup.send(f"Ошибка запроса account/info: {e}", ephemeral=True)
            return

        player_data = r2.get("data", {}).get(str(account_id), {})
        player_clan_id = player_data.get("clan_id", 0)
        player_nick = player_data.get("nickname", nick_value)

        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(interaction.user.id) if guild else None

        if player_clan_id != CLAN_ID:
            await interaction.followup.send(
                f"Игрок '{player_nick}' не в клане!",
                ephemeral=True
            )
            return
            
        if member:
            try:
                await member.edit(nick=f"{player_nick} ({name_value})")
            except Exception as e:
                await interaction.followup.send(f"Не удалось изменить ник: {e}", ephemeral=True)

            role_to_add = guild.get_role(ROLE_TO_ADD)
            role_to_remove = guild.get_role(ROLE_TO_REMOVE)

            if role_to_remove:
                await member.remove_roles(role_to_remove)
            if role_to_add:
                await member.add_roles(role_to_add)

        await interaction.followup.send(
            f"Авторизация успешна! Добро пожаловать в клан, {player_nick}!",
            ephemeral=True
        )

class AuthButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Авторизоваться", style=discord.ButtonStyle.green)
    async def auth(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AuthModal())


async def ensure_auth_message():
    await bot.wait_until_ready()
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        view = AuthButton()
        await channel.send("Нажмите кнопку для авторизации в клане:", view=view)


async def check_clan_members_continuous():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    role_to_check = guild.get_role(ROLE_TO_ADD)
    role_to_remove = guild.get_role(ROLE_TO_REMOVE)
    while True:
        if role_to_check:
            for member in role_to_check.members:
                try:
                    discord_nick = member.display_name
                    wot_nick = discord_nick.split("(")[0].strip() if "(" in discord_nick else discord_nick
                    r = requests.get("https://api.worldoftanks.eu/wot/account/list/", params={
                        "application_id": WOT_API_KEY,
                        "search": wot_nick,
                        "type": "exact",
                        "limit": 1
                    }, timeout=10).json()
                    data = r.get("data", [])
                    if not data:
                        await asyncio.sleep(60)
                        continue
                    if isinstance(data, dict):
                        account_id = list(data.keys())[0]
                    elif isinstance(data, list):
                        account_id = data[0].get("account_id")
                    else:
                        await asyncio.sleep(60)
                        continue
                    r2 = requests.get("https://api.worldoftanks.eu/wot/account/info/", params={
                        "application_id": WOT_API_KEY,
                        "account_id": account_id,
                        "fields": "clan_id"
                    }, timeout=10).json()
                    player_data = r2.get("data", {}).get(str(account_id), {})
                    player_clan_id = player_data.get("clan_id", 0)
                    if player_clan_id != CLAN_ID:
                        if role_to_check:
                            await member.remove_roles(role_to_check)
                        if role_to_remove:
                            await member.add_roles(role_to_remove)
                except:
                    pass
                await asyncio.sleep(60)
        await asyncio.sleep(60)

@bot.event
async def setup_hook():
    bot.loop.create_task(ensure_auth_message())
    bot.loop.create_task(check_clan_members_continuous())

keep_alive()
bot.run(os.getenv("TOKEN"))
