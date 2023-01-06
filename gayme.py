import discord
from enum import Enum
import datetime

#temp until DB
class Gaymes(Enum):
    csgo = 0
    dota = 1
    warcraft = 2
    necropolis = 3
    amogus = 4
    minecraft = 5
gaymes_names = {
    0: "Counter-Strike: Global Offensive",
    1: "Dota 2",
    2: "Warcraft 3",
    3: "Necropolis",
    4: "Among Us",
    5: "Minecraft"
}
gaymes_counts = {
    0: 5,
    1: 5,
    2: 2,
    3: 4,
    4: 4,
    5: 2
}

class GaymeDropdown(discord.ui.Select):
    def __init__(self):
        options = []
        for gayme in Gaymes:
            options.append(discord.SelectOption(label=gaymes_names[gayme.value])) 
        super().__init__(placeholder='Выбери игру', min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        view: GaymeView = self.view
        view.gayme_name = self.values[0]
        view.gayme_id = list(gaymes_names.keys())[list(gaymes_names.values()).index(view.gayme_name)]
        view.gayme_count = gaymes_counts[view.gayme_id]
        view.embed = generate_embed(view)
        view.remove_item(self)
        view.add_item(GaymeAcceptButton(row=1))
        view.add_item(GaymeMaybeButton(row=1))
        view.add_item(GaymeRejectButton(row=1))
        view.add_item(GaymePingButton(row=2))
        await interaction.response.edit_message(embed=self.view.embed,view=self.view)
        view.message = await interaction.original_response()


class GaymeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=3600)
        self.add_item(GaymeDropdown())
        self.gayme_name = None
        self.gayme_id = None
        self.embed = discord.Embed()
        gayme_count = None
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
    embed.title = view.gayme_name
    embed.remove_field(0)
    embed.insert_field_at(0,name="Игроки: ",value=f"{len(view.accepted)}/{view.gayme_count}",inline=False)
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
    if len(view.accepted) >= view.gayme_count:
        embed.color = discord.Color.green()
    else:
        embed.color = discord.Color.red()
    embed.set_footer(text=f"Последнее обновление: {datetime.datetime.now().isoformat(timespec='minutes').replace('T', ' ')}")
    return embed