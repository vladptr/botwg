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
CLAN_ID = 500242135
GUILD_ID = 1192735805068812288

TARGET_CHANNEL_ID = 1192780647429836818
ROLE_TO_ADD = 1192773043219615805
ROLE_TO_REMOVE = 1192784555921379389

class AuthModal(discord.ui.Modal, title="Авторизация в клане"):
    nick = discord.ui.TextInput(label="Никнейм в игре", placeholder="Введите никнейм")
    name = discord.ui.TextInput(label="Имя", placeholder="Ваше имя")
    ur = discord.ui.TextInput(label="Играешь укрепрайоны? (да/нет)", placeholder="да или нет")

    async def on_submit(self, interaction: discord.Interaction):
        nick_value = self.nick.value.strip()
        name_value = self.name.value.strip()

        try:
            r = requests.get("https://api.worldoftanks.eu/wot/account/list/", params={
                "application_id": WOT_API_KEY,
                "search": nick_value,
                "type": "exact",
                "limit": 1
            }, timeout=10).json()
            print("account/list response:", r)
        except Exception as e:
            await interaction.user.send(f"Ошибка запроса account/list: {e}")
            return

        data = r.get("data", [])
        account_id = None

        if isinstance(data, dict):
            if data:
                account_id = list(data.keys())[0]
        elif isinstance(data, list):
            if data:
                account_id = data[0].get("account_id")

        if not account_id:
            await interaction.user.send(f"Ошибка: игрок '{nick_value}' не найден! Ответ API: {r}")
            return

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

        player_data = r2.get("data", {}).get(str(account_id), {})
        player_clan_id = player_data.get("clan_id", 0)
        player_nick = player_data.get("nickname", nick_value)

        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(interaction.user.id) if guild else None

        if player_clan_id != CLAN_ID:
            await interaction.user.send(f"Ошибка: игрок '{player_nick}' не в клане! Ответ API: {player_data}")
        else:
            if member:
                try:
                    new_nick = f"{player_nick} ({name_value})"
                    await member.edit(nick=new_nick)
                except discord.Forbidden:
                    await interaction.user.send("Не могу изменить никнейм — недостаточно прав.")
                except discord.HTTPException as e:
                    print(f"Ошибка при смене ника: {e}")

                role_to_add = guild.get_role(ROLE_TO_ADD)
                role_to_remove = guild.get_role(ROLE_TO_REMOVE)
                try:
                    if role_to_remove:
                        await member.remove_roles(role_to_remove)
                    if role_to_add:
                        await member.add_roles(role_to_add)
                except discord.Forbidden:
                    await interaction.user.send("Недостаточно прав для изменения ролей.")
                except discord.HTTPException as e:
                    print(f"Ошибка при выдаче ролей: {e}")

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


async def check_clan_members_continuous():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Сервер не найден!")
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
                        print(f"{member.display_name} не найден в API")
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
                        print(f"{member.display_name} больше не в клане, меняем роли")
                        if role_to_check:
                            await member.remove_roles(role_to_check)
                        if role_to_remove:
                            await member.add_roles(role_to_remove)

                except Exception as e:
                    print(f"Ошибка при проверке {member.display_name}: {e}")

                await asyncio.sleep(60)
        await asyncio.sleep(60)


keep_alive()
bot.loop.create_task(check_clan_members_continuous())
bot.run(os.getenv("TOKEN"))
