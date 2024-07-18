import discord
import datetime
import sqlite3
import logging

logger = logging.getLogger("game")

conn = sqlite3.connect("data.db")
with conn:
    conn.execute("""CREATE TABLE IF NOT EXISTS gaymes (
        name string NOT NULL,
        players int,
        role int,
        server int
    );""")


class Game:
    def __init__(self, id, name, count, role):
        self.id = id - 1
        self.name = name
        self.count = count
        self.role = role

    def __str__(self):
        return f'{self.id}: "{self.name}" ({self.count} players)'

    def __repr__(self):
        return f"<Game: '{self.__str__()}' pings={self.role}>"


class GameDropdown(discord.ui.Select):
    def __init__(self, games):
        super().__init__(placeholder="Выбери игру", min_values=1, max_values=1)
        options = []
        for game in games:
            options.append(discord.SelectOption(label=game.name))
        self.options = options

    async def callback(self, interaction: discord.Interaction):
        view: GameView = self.view
        for game in view.games:
            if game.name == self.values[0]:
                view.game = game
        view.embed = generate_embed(view)
        view.remove_item(self)
        view.add_item(GameAcceptButton(row=1))
        view.add_item(GameMaybeButton(row=1))
        view.add_item(GameRejectButton(row=1))
        view.add_item(GamePingButton(row=2))
        await interaction.response.edit_message(embed=self.view.embed, view=self.view)
        logger.info(f"Created gathering for game {game.name}")
        if view.game.role is not None:
            await interaction.channel.send(
                content=f"<@&{view.game.role}> - собираемся!"
            )
        view.message = await interaction.original_response()


class GameView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=3600)
        self.guild = guild_id
        self.games = get_games(guild_id)
        self.add_item(GameDropdown(self.games))
        self.game = None
        self.embed = discord.Embed()
        self.accepted = []
        self.rejected = []
        self.notdecided = []
        self.message = None

    async def on_timeout(self):
        logger.info(f"Ended gathering for gayme {self.game.name}")
        self.clear_items().stop()
        await self.message.edit(view=self)


class GamePingButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(
            style=discord.ButtonStyle.primary, label="Труба зовет!", row=row
        )

    async def callback(self, interaction: discord.Interaction):
        logger.info(f"{interaction.user.display_name} pressed gather button")
        if len(self.view.accepted) < self.view.gayme.count:
            await interaction.response.send_message(
                content="Нас мало, куда трубить?", ephemeral=True, delete_after=10
            )
            return
        ping_string = ""
        for id in self.view.accepted:
            ping_string += f"<@{id}> "
        ping_string += " - труба зовет!"
        await interaction.response.send_message(content=ping_string)


class GameAcceptButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(style=discord.ButtonStyle.success, label="☑️", row=row)

    async def callback(self, interaction: discord.Interaction):
        user: discord.Member = interaction.user
        view: GameView = self.view
        logger.info(f"{user.display_name} applied for game {view.game.name}")
        if user.id in view.accepted:
            await interaction.response.send_message(
                content="Ты уже в игре!", ephemeral=True, delete_after=10
            )
            return
        if user.id in view.rejected:
            view.rejected.remove(user.id)
        if user.id in view.notdecided:
            view.notdecided.remove(user.id)
        view.accepted.append(user.id)
        embed = generate_embed(view)
        await interaction.response.edit_message(embed=embed)


class GameRejectButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(style=discord.ButtonStyle.danger, label="✖️", row=row)

    async def callback(self, interaction: discord.Interaction):
        user: discord.Member = interaction.user
        view: GameView = self.view
        logger.info(f"{user.display_name} rejected game {view.game.name}")
        if user.id in view.rejected:
            await interaction.response.send_message(
                content="Ты уже отказался!", ephemeral=True, delete_after=10
            )
            return
        if user.id in view.accepted:
            view.accepted.remove(user.id)
        if user.id in view.notdecided:
            view.notdecided.remove(user.id)
        view.rejected.append(user.id)
        embed = generate_embed(view)
        await interaction.response.edit_message(embed=embed)


class GameMaybeButton(discord.ui.Button):
    def __init__(self, row):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            emoji="<:thonk:1060266106629144686>",
            row=row,
        )

    async def callback(self, interaction: discord.Interaction):
        user: discord.Member = interaction.user
        view: GameView = self.view
        logger.info(f"{user.display_name} thinking about game {view.game.name}")
        if user.id in view.notdecided:
            await interaction.response.send_message(
                content="Ты все еще думаешь!", ephemeral=True, delete_after=10
            )
            return
        if user.id in view.accepted:
            view.accepted.remove(user.id)
        if user.id in view.rejected:
            view.rejected.remove(user.id)
        view.notdecided.append(user.id)
        embed = generate_embed(view)
        await interaction.response.edit_message(embed=embed)


def generate_embed(view: GameView):
    embed: discord.Embed = view.embed
    game: Game = view.game
    embed.title = game.name
    embed.remove_field(0)
    embed.insert_field_at(
        0, name="Игроки: ", value=f"{len(view.accepted)}/{game.count}", inline=False
    )
    embed.remove_field(1)
    accepted_value = "\n".join([f"<@{id}>" for id in view.accepted])
    if not accepted_value:
        accepted_value = "Пусто!"
    embed.insert_field_at(1, name="✅", value=accepted_value, inline=False)
    embed.remove_field(2)
    rejected_value = "\n".join([f"<@{id}>" for id in view.rejected])
    if not rejected_value:
        rejected_value = "Пусто!"
    embed.insert_field_at(2, name="❌", value=rejected_value, inline=False)
    embed.remove_field(3)
    thonk_value = "\n".join([f"<@{id}>" for id in view.notdecided])
    if not thonk_value:
        thonk_value = "Пусто!"
    embed.insert_field_at(3, name="Не определились", value=thonk_value, inline=False)
    if len(view.accepted) >= game.count:
        embed.color = discord.Color.green()
    else:
        embed.color = discord.Color.red()
    embed.set_footer(
        text=f"Последнее обновление: {datetime.datetime.now().isoformat(timespec='minutes').replace('T', ' ')}"
    )
    return embed


def get_games(guild):
    games = []
    for res in conn.execute(
        "SELECT rowid, name, players, role FROM gaymes WHERE server = ?", (guild,)
    ):
        games.append(Game(*res))
    logger.info(f"Parsed {len(games)} games from DB")
    return games


def add_game(name, count, role, guild):
    try:
        with conn:
            cnt = 0
            for res in conn.execute(
                "SELECT name FROM gaymes WHERE server=? AND name=?", (guild, name)
            ):
                cnt += 1
            if cnt > 0:
                logger.warning("Game already exists")
                return False
            with conn:
                conn.execute(
                    "INSERT INTO gaymes(name, players, role, server) VALUES (?, ?, ?, ?)",
                    (name, count, role, guild),
                )
        logger.info(f"Successfully added game {name} in {guild.name}")
        return True
    except sqlite3.Error:
        logger.error(f"Failed to add game in guild {guild.name}")
        return False


def edit_game(name, guild, count=2, role=None):
    try:
        with conn:
            cnt = 0
            for res in conn.execute(
                "SELECT name FROM gaymes WHERE server=? AND name=?", (guild, name)
            ):
                cnt += 1
            if cnt == 0:
                logger.warning("Game not exists")
                return False
            with conn:
                conn.execute(
                    "UPDATE gaymes SET players=?, role=? WHERE server=? AND name=?",
                    (count, role, guild, name),
                )
        logger.info(f"Successfully edited game {name} in {guild.name}")
        return True
    except sqlite3.Error:
        logger.error(f"Failed to edit game in guild {guild.name}")
        return False
