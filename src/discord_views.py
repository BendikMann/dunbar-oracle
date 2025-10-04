import discord
from discord import User, Guild, Member, Role
from discord.abc import Snowflake

import neo4j_connect
import postgres_connect


class DoYouKnow(discord.ui.View):

    def __init__(self, requester: Member, requestee: Member, role: Role, center: Member, *, timeout=180_000):
        super().__init__(timeout=timeout)
        # context needed to add role to appropriate user
        self.requester = requester
        self.requestee = requestee

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        relationships = neo4j_connect.Relationships()
        transaction_manager = postgres_connect.TransactionsManager()

        relationships.add_knowership(self.requestee.id, self.requester.id)

        # It is possible that the relationship adds centers that both nodes could not see.
        centers_requester = set(relationships.find_centers_about(self.requester.id))
        centers_requestee = set(relationships.find_centers_about(self.requestee.id))

        # This is just so we send fewer requests,
        for center in centers_requester.union(centers_requestee):
            transaction_manager.create_transaction(center)

        await interaction.message.edit(content="Thank you for responding. User will be added to your known list.",
                                       view=None)

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # TODO: dismiss user
        await interaction.message.edit(content="Thank you for responding. User will not be added to your known list.", view=None)
