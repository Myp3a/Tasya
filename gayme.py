import discord
from enum import Enum
import datetime
import sqlite3

conn = sqlite3.connect("data.db")
with conn:
    conn.execute("""CREATE TABLE IF NOT EXISTS gaymes (
        name string UNIQUE NOT NULL,
        players int,
        role int
    );""")

class Gayme:
    def __init__(self,id,name,count,role):
        self.id = id - 1
        self.name = name
        self.count = count
        self.role = role
    
    def __str__(self):
        return f"{self.id}: \"{self.name}\" ({self.count} players)"
    
    def __repr__(self):
        return f"<Gayme: '{self.__str__()}'>"

class GaymeDropdown(discord.ui.Select):
    def __init__(self,gaymes):
        super().__init__(placeholder='Выбери игру', min_values=1, max_values=1)
        options = []
        for gayme in gaymes:
            options.append(discord.SelectOption(label=gayme.name)) 
        self.options=options
    
    async def callback(self, interaction: discord.Interaction):
        view: GaymeView = self.view
        for gayme in view.gaymes:
            if gayme.name == self.values[0]:
                view.gayme_id = gayme.id
        view.embed = generate_embed(view)
        view.remove_item(self)
        view.add_item(GaymeAcceptButton(row=1))
        view.add_item(GaymeMaybeButton(row=1))
        view.add_item(GaymeRejectButton(row=1))
        view.add_item(GaymePingButton(row=2))
        await interaction.response.edit_message(content=f"<@&{view.gaymes[view.gayme_id].role}> - собираемся!",embed=self.view.embed,view=self.view)
        view.message = await interaction.original_response()


class GaymeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=3600)
        self.gaymes = []
        for res in conn.execute("SELECT rowid, name, players, role FROM gaymes"):
            self.gaymes.append(Gayme(*res))
        self.add_item(GaymeDropdown(self.gaymes))
        self.gayme_id = None
        self.embed = discord.Embed()
        self.accepted = []
        self.rejected = []
        self.notdecided = []
        self.message = None

    async def on_timeout(self):
        self.clear_items().stop()
        await self.message.edit(view=self)

class GaymePingButton(discord.ui.Button):
    def __init__(self,row):
        super().__init__(style=discord.ButtonStyle.primary,label="Труба зовет!",row=row)

    async def callback(self, interaction: discord.Interaction):
        if len(self.view.accepted) < self.view.gaymes[self.view.gayme_id].count:
            await interaction.response.send_message(content="Нас мало, куда трубить?",ephemeral=True,delete_after=10)
            return
        ping_string = ""
        for id in self.view.accepted:
            ping_string += f"<@{id}> "
        ping_string += " - труба зовет!"
        await interaction.response.send_message(content=ping_string)

class GaymeAcceptButton(discord.ui.Button):
    def __init__(self,row):
        super().__init__(style=discord.ButtonStyle.success,label="☑️",row=row)

    async def callback(self, interaction: discord.Interaction):
        user: discord.Member = interaction.user
        view: GaymeView = self.view
        if user.id in view.accepted:
            await interaction.response.send_message(content="Ты уже в игре!",ephemeral=True,delete_after=10)
            return
        if user.id in view.rejected:
            view.rejected.remove(user.id)
        if user.id in view.notdecided:
            view.notdecided.remove(user.id)
        view.accepted.append(user.id)
        embed = generate_embed(view)
        await interaction.response.edit_message(embed=embed)

class GaymeRejectButton(discord.ui.Button):
    def __init__(self,row):
        super().__init__(style=discord.ButtonStyle.danger,label="✖️",row=row)

    async def callback(self, interaction: discord.Interaction):
        user: discord.Member = interaction.user
        view: GaymeView = self.view
        if user.id in view.rejected:
            await interaction.response.send_message(content="Ты уже отказался!",ephemeral=True,delete_after=10)
            return
        if user.id in view.accepted:
            view.accepted.remove(user.id)
        if user.id in view.notdecided:
            view.notdecided.remove(user.id)
        view.rejected.append(user.id)
        embed = generate_embed(view)
        await interaction.response.edit_message(embed=embed)

class GaymeMaybeButton(discord.ui.Button):
    def __init__(self,row):
        super().__init__(style=discord.ButtonStyle.secondary,emoji="<:thonk:1060266106629144686>",row=row)

    async def callback(self, interaction: discord.Interaction):
        user: discord.Member = interaction.user
        view: GaymeView = self.view
        if user.id in view.notdecided:
            await interaction.response.send_message(content="Ты все еще думаешь!",ephemeral=True,delete_after=10)
            return
        if user.id in view.accepted:
            view.accepted.remove(user.id)
        if user.id in view.rejected:
            view.rejected.remove(user.id)
        view.notdecided.append(user.id)
        embed = generate_embed(view)
        await interaction.response.edit_message(embed=embed)

def generate_embed(view: GaymeView):
    embed: discord.Embed = view.embed
    gayme: Gayme = view.gaymes[view.gayme_id]
    embed.title = gayme.name
    embed.remove_field(0)
    embed.insert_field_at(0,name="Игроки: ",value=f"{len(view.accepted)}/{gayme.count}",inline=False)
    embed.remove_field(1)
    accepted_value = ""
    for id in view.accepted:
        accepted_value += f"<@{id}>\n"
    accepted_value.rstrip()
    if accepted_value == "":
        accepted_value = "Пусто!"
    embed.insert_field_at(1,name="✅",value=accepted_value,inline=False)
    embed.remove_field(2)
    rejected_value = ""
    for id in view.rejected:
        rejected_value += f"<@{id}>\n"
    rejected_value.rstrip()
    if rejected_value == "":
        rejected_value = "Пусто!"
    embed.insert_field_at(2,name="❌",value=rejected_value,inline=False)
    embed.remove_field(3)
    thonk_value = ""
    for id in view.notdecided:
        thonk_value += f"<@{id}>\n"
    thonk_value.rstrip()
    if thonk_value == "":
        thonk_value = "Пусто!"
    embed.insert_field_at(3,name="Не определились",value=thonk_value,inline=False)
    if len(view.accepted) >= gayme.count:
        embed.color = discord.Color.green()
    else:
        embed.color = discord.Color.red()
    embed.set_footer(text=f"Последнее обновление: {datetime.datetime.now().isoformat(timespec='minutes').replace('T', ' ')}")
    return embed

def add_gayme(name, count, role):
    try:
        with conn:
            conn.execute("INSERT INTO gaymes(name, players, role) VALUES (?, ?, ?)",(name, count, role))
        return True
    except:
        return False