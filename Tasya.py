#!/usr/bin/python3
# # -*- coding: utf-8 -*-


import asyncio
import coloredlogs
import logging
import config
import sys
import io
import base64
import discord
from discord import app_commands

from game import GameView, add_game, edit_game, get_games
from music import MusicController
from talk import generate
from stt import recognize
from image import caption

coloredlogs.install(
    level="INFO",
    fmt="[{asctime}] [{levelname:<8}] {name}: {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("main")


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
            if sys.argv[1] == "-u":
                logger.warning("Syncing command tree")
                await self.tree.sync()


client = MyClient()


@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user} (ID: {client.user.id})")
    logger.info("------")


music_grp = app_commands.Group(name="music", description="Музычка")


@client.tree.command()
async def game(interaction: discord.Interaction):
    """Поиграть с друзьяшками"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /game"
    )
    view = GameView(interaction.guild_id)
    if len(view.games) == 0:
        await interaction.response.send_message(
            content="Сначала добавь хоть одну игру!"
        )
    else:
        await interaction.response.send_message(view=view)


@client.tree.command()
@app_commands.describe(
    name="Название игры",
    player_count="Необходимое количество игроков",
    role="Роль, которую пингуем при сборе",
)
async def gaymeadd(
    interaction: discord.Interaction,
    name: str,
    player_count: app_commands.Range[int, 2, 20],
    role: discord.Role,
):
    """Добавить новую игру в список"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /gameadd"
    )
    res = add_game(name, player_count, role.id, interaction.guild_id)
    if res:
        await interaction.response.send_message(content="Игра успешно добавлена!")
    else:
        await interaction.response.send_message(content="Ошибка при добавлении.")


@client.tree.command()
@app_commands.describe(
    name="Название игры",
    player_count="Необходимое количество игроков",
    role="Роль, которую пингуем при сборе",
)
async def gaymeedit(
    interaction: discord.Interaction,
    name: str,
    player_count: app_commands.Range[int, 2, 20],
    role: discord.Role,
):
    """Отредактировать игру"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /gameedit"
    )
    games = get_games(interaction.guild_id)
    sel_game = None
    for game in games:
        if game.name == name:
            sel_game = game
    if sel_game is None:
        await interaction.response.send_message(content="Такой игры не существует.")
        return
    res = edit_game(name, interaction.guild_id, player_count, role.id)
    if res:
        await interaction.response.send_message(
            content=f"**{name}** успешно обновлена!"
        )
    else:
        await interaction.response.send_message(content="Ошибка при обновлении.")


@music_grp.command(name="play")
@app_commands.describe(link="Ссылка или запрос")
async def music_play(interaction: discord.Interaction, link: str):
    """Добавить песню в очередь"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music play"
    )
    if (player := client.music.get_player(interaction.guild)) is None:
        if (voice := interaction.user.voice) is not None:
            player = await client.music.connect(voice.channel)
        else:
            return await interaction.response.send_message(
                "Вы не в голосовом канале!", delete_after=30
            )
    res = await player.queue(link)
    await interaction.response.send_message(
        f"[{res['title']}]({res['url']}) добавлено в очередь"
    )


@music_grp.command(name="pause")
async def music_pause(interaction: discord.Interaction):
    """Поставить на паузу"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music pause"
    )
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message(
            "Ничего не играет!", delete_after=30
        )
    player.pause()
    await interaction.response.send_message("Поставлено на паузу.", delete_after=30)


@music_grp.command(name="resume")
async def music_resume(interaction: discord.Interaction):
    """Продолжить воспроизведение"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music resume"
    )
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message(
            "Ничего не играет!", delete_after=30
        )
    player.resume()
    await interaction.response.send_message("Продолжаю.", delete_after=30)


@music_grp.command(name="skip")
async def music_skip(interaction: discord.Interaction):
    """Включить следующую песню"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music skip"
    )
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message(
            "Ничего не играет!", delete_after=30
        )
    player.skip()
    await interaction.response.send_message("Включаю следующую...", delete_after=30)


@music_grp.command(name="volume")
@app_commands.describe(volume="Громкость")
async def music_volume(
    interaction: discord.Interaction, volume: app_commands.Range[int, 1, 100]
):
    """Установить громкость"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music volume"
    )
    if (player := client.music.get_player(interaction.guild)) is None:
        return await interaction.response.send_message(
            "Ничего не играет!", delete_after=30
        )
    player.set_volume(volume / 100)
    await interaction.response.send_message(
        f"Громкость установлена на {volume}", delete_after=30
    )


@music_grp.command(name="stop")
async def music_stop(interaction: discord.Interaction):
    """Остановить музыку"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music stop"
    )
    if client.music.get_player(interaction.guild) is None:
        return await interaction.response.send_message(
            "Ничего не играет!", delete_after=30
        )
    await client.music.destroy_player(interaction.guild)
    await interaction.response.send_message("Музыка выключена.", delete_after=30)


@music_grp.command(name="now")
async def music_now(interaction: discord.Interaction):
    """Что сейчас играет"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music now"
    )
    if client.music.get_player(interaction.guild) is None:
        return await interaction.response.send_message(
            "Ничего не играет!", delete_after=30
        )
    await interaction.response.send_message(
        embed=await client.music.now(interaction.guild)
    )


@music_grp.command(name="queue")
async def music_queue(interaction: discord.Interaction):
    """Очередь песен"""
    logger.info(
        f"({interaction.guild.name}) {interaction.user.display_name} used /music queue"
    )
    if client.music.get_player(interaction.guild) is None:
        return await interaction.response.send_message(
            "Ничего не играет!", delete_after=30
        )
    await interaction.response.send_message(
        embed=await client.music.queue(interaction.guild)
    )


client.tree.add_command(music_grp)


@client.event
async def on_message(message):
    if message.author == client.user:
        logger.info(
            f"({message.guild.name}) {client.user.display_name}: {message.content}"
        )
        return
    for att in message.attachments:
        if att.filename == "voice-message.ogg":
            logger.info(
                f"({message.guild.name}) {message.author.display_name}: *voice message*"
            )
            spoken_text = await recognize(await att.read())
            if spoken_text != "":
                await message.reply(spoken_text)
    ref = message.reference
    if ref is not None:
        ref = ref.resolved
        if ref is not None:
            ref = ref.author
    if (
        "Тас" in message.content
        or ref == client.user
        or client.user in message.mentions
    ):
        logger.info(
            f"({message.guild.name}) {message.author.display_name}: {message.content}"
        )
        logger.info("I was mentioned")
        messages = [
            hist_message async for hist_message in message.channel.history(limit=50)
        ]
        cntr_you = 0
        cont = ""
        for hist_message in messages:
            text = hist_message.clean_content.replace("\n", " ")
            for att in hist_message.attachments:
                if "image" in att.content_type:
                    img_stream = io.BytesIO()
                    await att.save(img_stream)
                    b64_bytes = base64.b64encode(img_stream.getvalue())
                    img_caption = await caption(b64_bytes.decode())
                    text += (
                        "\n<|start_header_id|>model<|end_header_id|>*shows <|model|> a picture of "
                        + img_caption
                        + "*<|eot_id|>"
                    )
            if hist_message.author == client.user:
                name = "<|start_header_id|>model<|end_header_id|>"
            else:
                name = "<|start_header_id|>user<|end_header_id|>"
                cntr_you += 1
            cont = name + ": " + text + "<|eot_id|>\n" + cont
            if cntr_you > 14:
                break
        async with message.channel.typing():
            resp = await generate(config.prompt, cont, client.talk_lock)
        await message.reply(resp)


client.run(config.bot_token, log_level=logging.DEBUG, log_handler=logging.NullHandler())
