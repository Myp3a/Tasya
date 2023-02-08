# inspired by https://gist.github.com/EvieePy/ab667b74e9758433b3eb806c53a19f34

import asyncio
import discord
import json
import os
from datetime import date
from functools import partial
from youtube_dl import YoutubeDL

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'tmp/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)

class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, data):
        super().__init__(source)
        
        self.title = data.get('title')
        self.url = data.get('url')
        self.channel = data.get('channel')
        self.upload_date = data.get('upload_date')
        self.duration = data.get('duration')
        self.id = data.get('id')
        self.thumbnail = data.get('thumbnail')
        # self.like_count = data.get('like_count')
        self.view_count = data.get('view_count')

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, url):
        loop = asyncio.get_running_loop()

        to_run = partial(ytdl.extract_info, url=url, download=False)
        data = await loop.run_in_executor(None, to_run)

        # data.pop('formats')
        # data.pop('automatic_captions')
        # print(json.dumps(data,indent=2))

        # playlist extraction
        if 'entries' in data:
            data = data['entries'][0]

        return {'url': data['webpage_url'], 'title': data['title'], 'channel': data['channel'], 
                'upload_date': data['upload_date'], 'duration':  data['duration'], 
                'view_count': data['view_count'], #'like_count': data['like_count'],
                'id': data['id'], 'thumbnail': data['thumbnail']}

    @classmethod
    async def regather_stream(cls, data):
        loop = asyncio.get_running_loop()

        to_run = partial(ytdl.extract_info, url=data['url'], download=False)
        stream_data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(stream_data['url']), data=data)

class MusicController:
    def __init__(self):
        self.players = {}
        if not os.path.exists("tmp"):
            os.makedirs("tmp")

    def create_player(self,voice):
        player = Player(voice)
        asyncio.get_running_loop().create_task(self.destruct_after_timeout(voice.guild,player))
        self.players[voice.guild.id] = player
        return player

    def get_player(self,guild):
        player = self.players.get(guild.id, None)
        return player

    async def destruct_after_timeout(self,guild,player):
        await player.destroyed.wait()
        await self.destroy_player(guild)

    async def destroy_player(self,guild):
        player = self.players.get(guild.id, None)
        if player is None:
            return
        player.destroyed.set()
        player.stop()
        await player.voice_client.disconnect()
        self.players.pop(guild.id, None)

    async def connect(self,voice):
        if (player := self.get_player(voice.guild)) is None:
            vc = await voice.connect()
            return self.create_player(vc)
        await player.voice_client.move_to(voice)
        return player

    async def now(self,guild):
        if (player := self.players.get(guild.id, None)) is None:
            return
        now_data = await player.now()
        embed = discord.Embed()
        embed.title = now_data['title']
        embed.url = now_data['url']
        embed.color = discord.Color.red()
        embed.add_field(name="**Автор**",value=now_data['channel'],inline=False)
        embed.add_field(name="**Длительность**",value=(f"{str(now_data['duration'] // 3600) + ':' if now_data['duration'] > 3600 else ''}"
                                                   f"{now_data['duration'] % 3600 // 60:02}:"
                                                   f"{now_data['duration'] % 60:02}")
                                                   ,inline=False)
        embed.add_field(name="Дата выхода",value=f"{date.fromisoformat(now_data['upload_date']):%d.%m.%Y}",inline=False)
        embed.add_field(name="Просмотры",value=f"{now_data['view_count']:,}")
        # embed.add_field(name="Лайки",value=now_data['like_count'])
        
        embed.set_image(url=now_data['thumbnail'])
        return embed

    async def queue(self,guild):
        if (player := self.players.get(guild.id, None)) is None:
            return
        embed = discord.Embed()
        embed.title = "Очередь"
        embed.color = discord.Color.red()
        queue_text = ""
        for song in await player.queue_info():
            queue_text += f"[{song['title']}]({song['url']})\n"
        if queue_text != "":
            embed.add_field(name="Следующие песни:",value=queue_text)
        return embed

class Player:
    def __init__(self,voice_client):
        self._queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.playing = asyncio.Event()
        self.destroyed = asyncio.Event()
        self.volume = .5
        self.voice_client = voice_client
        asyncio.get_running_loop().create_task(self.loop())
    
    async def loop(self):
        while True:
            if self.destroyed.is_set():
                return
            self.next.clear()
            
            try:
                async with asyncio.timeout(600):
                    source = await self._queue.get()
                    self.playing.set()
            except asyncio.TimeoutError:
                self.destroyed.set()
                continue

            source = await YTDLSource.regather_stream(source)

            source.volume = self.volume
            self.current = source

            self.voice_client.play(source, after=lambda _: self.next.set())

            await self.next.wait()

            source.cleanup()
            self.current = None
            self.playing.clear()

    async def queue(self,link):
        src = await YTDLSource.create_source(link)
        await self._queue.put(src)
        return src
    
    async def queue_info(self):
        all = []
        for i in range(self._queue.qsize()):
            item = self._queue.get_nowait()
            self._queue.task_done()
            self._queue.put_nowait(item)
            all.append(item)
        return all

    async def now(self):
        return self.current

    async def _pause_watcher(self):
        try:
            async with asyncio.timeout(600):
                await self.playing.wait()
        except asyncio.TimeoutError:
            self.destroyed.set()
            return
        
    def pause(self):
        if not self.voice_client.is_paused():
            self.voice_client.pause()
            self.playing.clear()
            asyncio.get_running_loop().create_task(self._pause_watcher())

    def resume(self):
        if self.voice_client.is_paused():
            self.voice_client.resume()
            self.playing.set()
        
    def stop(self):
        for _ in range(self._queue.qsize()):
            self._queue.get_nowait()
            self._queue.task_done()
        self.voice_client.stop()

    def skip(self):
        if self.playing.is_set():
            self.voice_client.stop()

    def set_volume(self,volume):
        if self.voice_client.source:
            self.voice_client.source.volume = volume
