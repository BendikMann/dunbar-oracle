import discord


class WhoYouKnow(discord.ui.View, title='Who do you know?'):
    def __init__(self, *, timeout=180_000):
        super().__init__(timeout=timeout)

    @discord.ui.UserSelect
    async def on_who_you_know(self, ctx):
        pass

class DoYouKnow(discord.ui.View, title='Do you know?'):


    def __init__(self, *, timeout=180_000):
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # TODO: Add user to the graph of known user
        await interaction.response.send(content="Thank you for your response")


    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        # TODO: dismiss user
        await interaction.response.send(content="Thank you for responding. User will not be added to your known list.")
