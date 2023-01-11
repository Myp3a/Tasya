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

from gayme import GaymeView, add_gayme

coloredlogs.install(level='INFO',fmt='[{asctime}] [{levelname:<8}] {name}: {message}', style='{', datefmt='%Y-%m-%d %H:%M:%S')

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
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

client.run(config.bot_token,log_level=logging.DEBUG,log_handler=logging.NullHandler())