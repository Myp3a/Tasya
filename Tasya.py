#!/usr/bin/python3
# # -*- coding: utf-8 -*-

from typing import Literal, Union, NamedTuple
from enum import Enum

import coloredlogs
import logging
import config
import datetime
import sys
import discord
from discord import app_commands

from gayme import GaymeView, add_gayme, edit_gayme, get_gaymes
from pidor import select_gay, gay_stats

coloredlogs.install(level='INFO',fmt='[{asctime}] [{levelname:<8}] {name}: {message}', style='{', datefmt='%Y-%m-%d %H:%M:%S')

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if len(sys.argv) > 1:
            if sys.argv[1] == '-u':
                await self.tree.sync()


client = MyClient()

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

@client.tree.command()
async def gayme(interaction: discord.Interaction):
    """Поиграть с друзьяшками"""
    view = GaymeView(interaction.guild_id)
    if len(view.gaymes) == 0:
        await interaction.response.send_message(content="Сначала добавь хоть одну игру!")
    else:
        await interaction.response.send_message(view=view)

@client.tree.command()
@app_commands.describe(name="Название игры", player_count="Необходимое количество игроков", role="Роль, которую пингуем при сборе")
async def gaymeadd(interaction: discord.Interaction, name: str, player_count: app_commands.Range[int, 2, 20], role: discord.Role = None):
    """Добавить новую игру в список"""
    if role is None:
        roleid = None
    else:
        roleid = role.id
    res = add_gayme(name, player_count, roleid, interaction.guild_id)
    if res:
        await interaction.response.send_message(content="Игра успешно добавлена!")
    else:
        await interaction.response.send_message(content="Ошибка при добавлении.")

@client.tree.command()
@app_commands.describe(name="Название игры", player_count="Необходимое количество игроков", role="Роль, которую пингуем при сборе")
async def gaymeedit(interaction: discord.Interaction, name: str, player_count: app_commands.Range[int, 2, 20] = None, role: discord.Role = None):
    """Отредактировать игру"""
    gaymes = get_gaymes(interaction.guild_id)
    sel_gayme = None
    for gayme in gaymes:
        if gayme.name == name:
            sel_gayme = gayme
    if sel_gayme is None:
        await interaction.response.send_message(content="Такой игры не существует.")
        return
    if role is None:
        roleid = sel_gayme.role
    else:
        roleid = role.id
    if player_count is None:
        player_count = sel_gayme.count
    res = edit_gayme(name, interaction.guild_id, player_count, roleid)
    if res:
        await interaction.response.send_message(content="Игра успешно обновлена!")
    else:
        await interaction.response.send_message(content="Ошибка при обновлении.")

@client.tree.command()
@app_commands.describe(period="Период статистики")
async def pidor(interaction: discord.Interaction, period: Literal["Месяц", "Год", "Все время"] = None):
    """Выборы, выборы - кандидаты - пидоры!"""
    if period is None:
        res = select_gay(interaction.guild)
        await interaction.response.send_message(content=res[0])
        for msg in res[1:]:
            await interaction.channel.send(msg)
    else:
        res = gay_stats(interaction.guild, period)
        await interaction.response.send_message(embed=res)

client.run(config.bot_token,log_level=logging.DEBUG,log_handler=logging.NullHandler())