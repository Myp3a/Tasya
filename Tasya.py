#!/usr/bin/python3
# # -*- coding: utf-8 -*-

from typing import Literal, Union, NamedTuple
from enum import Enum

import asyncio
import coloredlogs
import logging
import config
import datetime
import sys
import discord
from discord import app_commands

from gayme import GaymeView, add_gayme, edit_gayme, get_gaymes
from pidor import select_gay, gay_stats, set_gay_role
from music import MusicController
from talk import generate
from stt import recognize

coloredlogs.install(level='INFO',fmt='[{asctime}] [{levelname:<8}] {name}: {message}', style='{', datefmt='%Y-%m-%d %H:%M:%S')

class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.music = MusicController()
        self.talk_lock = asyncio.Lock()

    async def setup_hook(self):
        if len(sys.argv) > 1:
            if sys.argv[1] == '-u':
                await self.tree.sync()


client = MyClient()

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')

music_grp = app_commands.Group(name="music", description="Музычка")

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
        await interaction.response.send_message(content=f"**{name}** успешно обновлена!")
    else:
        await interaction.response.send_message(content="Ошибка при обновлении.")

@client.tree.command()
@app_commands.describe(period="Период статистики")
async def pidor(interaction: discord.Interaction, period: Literal["Месяц", "Год", "Все время"] = None):
    """Выборы, выборы - кандидаты - пидоры!"""
    if period is None:
        res = await select_gay(interaction.guild)
        await interaction.response.send_message(content=res[0])
        for msg in res[1:]:
            await interaction.channel.send(msg)
    else:
        res = gay_stats(interaction.guild, period)
        await interaction.response.send_message(embeds=res)

@client.tree.command()
@app_commands.describe(role="Роль для пидора")
async def pidorrole(interaction: discord.Interaction, role: discord.Role = None):
    """Званием пидора объявляется..."""
    if set_gay_role(interaction.guild, role):
        if role is None:
            await interaction.response.send_message(content=f"Роль удалена.")
        else:
            await interaction.response.send_message(content=f"Роль изменена на {role.mention}")
    else:
        await interaction.response.send_message(content="Ошибка выполнения.")

@music_grp.command(name="play")
@app_commands.describe(link="Ссылка или запрос")
async def music_play(interaction: discord.Interaction, link: str):
    """Добавить песню в очередь"""
    if (player := client.music.get_player(interaction.guild)) is None:
        if not (voice := interaction.user.voice) is None:
            player = await client.music.connect(voice.channel)
        else:
            return await interaction.response.send_message("Вы не в голосовом канале!",delete_after=30)
    res = await player.queue(link)
    await interaction.response.send_message(f"[{res['title']}]({res['url']}) добавлено в очередь")

@music_grp.command(name="pause")
async def music_pause(interaction: discord.Interaction):
    """Поставить на паузу"""
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message("Ничего не играет!",delete_after=30)
    player.pause()
    await interaction.response.send_message("Поставлено на паузу.",delete_after=30)

@music_grp.command(name="resume")
async def music_resume(interaction: discord.Interaction):
    """Продолжить воспроизведение"""
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message("Ничего не играет!",delete_after=30)
    player.resume()
    await interaction.response.send_message("Продолжаю.",delete_after=30)
 
@music_grp.command(name="skip")
async def music_skip(interaction: discord.Interaction):
    """Включить следующую песню"""
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message("Ничего не играет!",delete_after=30)
    player.skip()
    await interaction.response.send_message("Включаю следующую...",delete_after=30)

@music_grp.command(name="volume")
@app_commands.describe(volume="Громкость")
async def music_volume(interaction: discord.Interaction, volume: app_commands.Range[int,1,100]):
    """Установить громкость"""
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message("Ничего не играет!",delete_after=30)
    player.set_volume(volume / 100)
    await interaction.response.send_message(f"Громкость установлена на {volume}",delete_after=30)

@music_grp.command(name="stop")
async def music_stop(interaction: discord.Interaction):
    """Остановить музыку"""
    if client.music.get_player(interaction.guild) is None:
        return await interaction.response.send_message("Ничего не играет!",delete_after=30)
    await client.music.destroy_player(interaction.guild)
    await interaction.response.send_message("Музыка выключена.",delete_after=30)

@music_grp.command(name="now")
async def music_now(interaction: discord.Interaction):
    """Что сейчас играет"""
    if client.music.get_player(interaction.guild) is None:
        return await interaction.response.send_message("Ничего не играет!",delete_after=30)
    await interaction.response.send_message(embed=await client.music.now(interaction.guild))

@music_grp.command(name="queue")
async def music_queue(interaction: discord.Interaction):
    """Очередь песен"""
    if client.music.get_player(interaction.guild) is None:
        return await interaction.response.send_message("Ничего не играет!",delete_after=30)
    await interaction.response.send_message(embed=await client.music.queue(interaction.guild))

client.tree.add_command(music_grp)

# @client.tree.command()
# async def say(interaction: discord.Interaction):
#     """Попизди мне тут."""
#     chatlog = ""
#     messages = [message async for message in interaction.channel.history(limit=50)]
#     for message in messages[::-1]:
#         name = "You"
#         if message.author == client.user:
#             name = "Tasya"
#         text = message.clean_content.replace("\n"," ")
#         chatlog += f"{name}: {text}\n"
#     chatlog = chatlog.strip()
#     await interaction.response.defer(thinking=True)
#     resp = await generate(config.chardef,config.exdialog,chatlog)
#     await interaction.followup.send(resp)
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    for att in message.attachments:
        if att.filename == "voice-message.ogg":
            spoken_text = await recognize(await att.read())
            if spoken_text != "":
                await message.reply(spoken_text)
    ref = message.reference
    if not ref is None:
        ref = ref.resolved
        if not ref is None:
            ref = ref.author
    if "Тася" in message.content or ref == client.user:
        messages = [hist_message async for hist_message in message.channel.history(limit=50)]
        cntr_you = 0
        cont = ""
        for hist_message in messages:
            text = hist_message.clean_content.replace("\n", " ")
            if hist_message.author == client.user:
                name = "<|model|>"
            else:
                name = "<|user|>"
                cntr_you += 1
            cont = name + ": " + text + "\n" + cont
            if cntr_you > 14:
                break
        async with message.channel.typing():
            resp = await generate(config.prompt,cont,client.talk_lock)
        await message.reply(resp)

client.run(config.bot_token,log_level=logging.DEBUG,log_handler=logging.NullHandler())
