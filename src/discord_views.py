import discord
from discord import User, Guild, Member, Role
from discord.abc import Snowflake

import neo4j_connect


class DoYouKnow(discord.ui.View):


    def __init__(self, requester: Member, requestee: Member, role: Role, center: Member, *, timeout=180_000):
        super().__init__(timeout=timeout)
        # context needed to add role to appropriate user
        self.requester = requester
        self.requestee = requestee
        self.role = role
        self.center = center

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        relationships = neo4j_connect.Relationships()
        relationships.add_knowership(interaction.user.id, self.requester.id)
        await interaction.message.edit(content="Thank you, friendship established")
        # Now we check to see if anyone is friends with the center now.
        # TODO: Implement depth from center, maybe include in reason
        if relationships.are_snowflake_friends(self.requester.id, self.center.id):
            await self.requester.add_roles(self.role, reason=f"User now has path to {self.center.name}")

        if relationships.are_snowflake_friends(self.requestee.id, self.center.id):
            await self.requestee.add_roles(self.role, reason=f"User now has path to {self.center.name}")

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # TODO: dismiss user
        await interaction.user.send(content="Thank you for responding. User will not be added to your known list.")
