import discord
from discord.ext import commands
import requests
import os
from webservis import keep_alive

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

WOT_API_KEY = "97d79abe59b0145f55a621ab80ad9a22"
CLAN_ID = 500242135

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

            r = requests.get("https://api.worldoftanks.eu/wot/account/list/", params={
                "application_id": WOT_API_KEY,
                "search": nick_value,
                "type": "startswith",
                "limit": 5
            }, timeout=10).json()

            data = r.get("data", [])
            if not data:
                await interaction.user.send(f"Игрок '{nick_value}' не найден! Ответ API: {r}")
                return

            if isinstance(data, dict):
                account_id = list(data.keys())[0]
            elif isinstance(data, list):
                account_id = data[0].get("account_id")
            else:
                await interaction.user.send("Неверный формат ответа API!")
                return

            r2 = requests.get("https://api.worldoftanks.eu/wot/account/info/", params={
                "application_id": WOT_API_KEY,
                "account_id": account_id,
                "fields": "clan_id,nickname"
            }, timeout=10).json()

            player_data = r2.get("data", {}).get(str(account_id), {})
            player_clan_id = player_data.get("clan_id", 0)
            player_nick = player_data.get("nickname", nick_value)

            # Получаем участника сервера
            guild = interaction.guild
            member = guild.get_member(interaction.user.id)

            if player_clan_id != CLAN_ID:
                try:
                    await interaction.user.send(f"Ошибка: игрок '{player_nick}' не в клане! Ответ API: {player_data}")
                except discord.Forbidden:
                    await interaction.response.send_message(
                        f"Не могу отправить ЛС, {interaction.user.mention}, включите прием сообщений от участников сервера.",
                        ephemeral=True
                    )
                return

            role_to_add = guild.get_role(ROLE_TO_ADD)
            role_to_remove = guild.get_role(ROLE_TO_REMOVE)
            if role_to_remove:
                await member.remove_roles(role_to_remove)
            if role_to_add:
                await member.add_roles(role_to_add)

            try:
                await interaction.user.send(f"Добро пожаловать в клан '{player_nick} ({name_value})'!")
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"Не могу отправить ЛС, {interaction.user.mention}, включите прием сообщений от участников сервера.",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Ошибка в on_submit: {e}")
            try:
                await interaction.user.send(f"Произошла внутренняя ошибка: {e}")
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"Произошла внутренняя ошибка: {e}", ephemeral=True
                )


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
