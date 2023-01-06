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

from gayme import GaymeView

coloredlogs.install(level='INFO',fmt='[{asctime}] [{levelname:<8}] {name}: {message}', style='{', datefmt='%Y-%m-%d %H:%M:%S')

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print(sys.argv)
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
    view = GaymeView()
    await interaction.response.send_message(view=view)

client.run(config.bot_token,log_level=logging.DEBUG,log_handler=logging.NullHandler())