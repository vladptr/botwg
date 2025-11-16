import discord
from discord.ext import commands
import requests
import os
from webservis import keep_alive

try:
    RENDER_IP = requests.get("https://api.ipify.org", timeout=5).text
    print(f"Публичный IP Render: {RENDER_IP}")
except Exception as e:
    print(f"Не удалось определить IP Render: {e}")
    RENDER_IP = None

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
        try:
            nick_value = self.nick.value.strip()
            name_value = self.name.value.strip()
            ur_value = self.ur.value.lower().strip()

            params = {
                "application_id": WOT_API_KEY,
                "search": nick_value,
                "type": "startswith",
                "limit": 5
            }

            r = requests.get("https://api.worldoftanks.eu/wot/account/list/", params=params, timeout=10).json()
            print("account/list response:", r)

            data = r.get("data", [])
            account_id = None

            if isinstance(data, dict):
                for acc_id, info in data.items():
                    if info.get("nickname", "").upper() == nick_value.upper():
                        account_id = acc_id
                        break
                if not account_id and data:
                    account_id = list(data.keys())[0]
            elif isinstance(data, list):
                for info in data:
                    if info.get("nickname", "").upper() == nick_value.upper():
                        account_id = info.get("account_id")
                        break
                if not account_id and data:
                    account_id = data[0].get("account_id")

            if not account_id:
                await interaction.user.send(f"Ошибка: игрок '{nick_value}' не найден! Ответ API: {r}")
                return

            r2 = requests.get("https://api.worldoftanks.eu/wot/account/info/", params={
                "application_id": WOT_API_KEY,
                "account_id": account_id,
                "fields": "clan_id,nickname"
            }, timeout=10).json()
            print("account/info response:", r2)

            player_data = r2.get("data", {}).get(account_id, {})
            player_clan_id = player_data.get("clan_id", 0)
            player_nick = player_data.get("nickname", nick_value)

            if player_clan_id != int(CLAN_ID):
                await interaction.user.send(f"Ошибка: игрок '{player_nick}' не в клане! Ответ API: {player_data}")
                return

            guild = interaction.guild
            if not guild:
                await interaction.user.send("Ошибка: невозможно получить сервер (guild is None).")
                return

            member = guild.get_member(interaction.user.id)
            if not member:
                await interaction.user.send("Ошибка: невозможно найти участника на сервере.")
                return

            role_to_add = guild.get_role(ROLE_TO_ADD)
            role_to_remove = guild.get_role(ROLE_TO_REMOVE)

            if role_to_remove:
                await member.remove_roles(role_to_remove)
            if role_to_add:
                await member.add_roles(role_to_add)

            await interaction.user.send(f"Добро пожаловать в клан '{player_nick} ({name_value})'!")

        except Exception as e:
            import traceback
            traceback.print_exc()
            try:
                await interaction.user.send(f"Произошла ошибка при авторизации: {e}")
            except:
                pass

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
