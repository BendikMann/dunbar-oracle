import os

import discord
from discord import app_commands, Guild
from discord.abc import Snowflake
from discord.app_commands import command, commands
from dotenv import load_dotenv

import neo4j_connect
import logging

from discord_views import DoYouKnow

intents = discord.Intents.default()
intents.members = True

description = '''
A bot that tracks the relationship of people in a discord.

It does this by asking each user who joins a simple question:

Who do you know?

The user they are claimed to know is then sent a message asking, 'Do you know ___?'

If so, 
'''

class known_role(Snowflake):
    id = 1353215817227173960

class MY_GUILD(Snowflake):
    id = 386361143511351296

class center_user(Snowflake):
    id = 121801869281460228

class DunbarClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

client = DunbarClient(intents=intents)


@client.tree.command(
    name='iknow',
    description='Note that you know this user'
)
@discord.app_commands.describe(member="Member to mark as known by you.")
async def iknow(interaction: discord.Interaction, member: discord.Member):
    # TODO: add database hook
    relationships = neo4j_connect.Relationships()

    requester_snowflake = interaction.user.id
    knowee_snowflake = member.id

    # Does requester exist?
    if not relationships.does_snowflake_exists(requester_snowflake):
        logging.info(f'Creating snowflake: {requester_snowflake}, {interaction.user.name}')
        relationships.create_user(requester_snowflake)

    # Does Knowee exist
    if not relationships.does_snowflake_exists(knowee_snowflake):
        logging.info(f'Creating snowflake: {knowee_snowflake}, {member.name}')
        relationships.create_user(knowee_snowflake)

    # Add relationship
    logging.info(f'Making knowership of {requester_snowflake}({interaction.user.name}) -> {knowee_snowflake}({member.name})')
    relationships.add_knowership(requester_snowflake, knowee_snowflake)
    # TODO: what happens when a person already has a relationship?


    await interaction.response.send_message(f'{member} marked as known by you.', ephemeral=True)
    # Ask the knowee if they know the requester, establishing friendship.
    await dm_confirm_knowership(requester_snowflake, knowee_snowflake,interaction.guild)


async def dm_confirm_knowership(requester_snowflake, target_snowflake, guild: Guild):
    # We assume that the users already exist, because they would be created by the iknow command
    # additionally we fetch them by guild so that we can apply the needed role.
    requester = await guild.fetch_member(requester_snowflake)
    target = await guild.fetch_member(target_snowflake)

    role_instance = guild.get_role(known_role.id)
    center_instance = guild.get_member(center_user.id)

    await target.send(content=f"Do you know {requester.display_name}?", view=DoYouKnow(requester, target, role_instance, center_instance))


    pass

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

"""
When a member joins we need to DM them to see who they are friends with.
"""
@client.event
async def on_member_join(member):
    pass



if __name__ == '__main__':
    # Load in .env file
    load_dotenv()
    client.run(os.getenv('DISCORD_TOKEN'))