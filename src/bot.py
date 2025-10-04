import asyncio
import os

import discord
import table2ascii
from discord import app_commands, Guild, guild
from discord.abc import Snowflake
from discord.app_commands import command, commands
from discord.ext import tasks
from discord.ext.commands import has_guild_permissions, has_permissions
from dotenv import load_dotenv
from table2ascii import PresetStyle

import neo4j_connect
import logging

import postgres_connect
from discord_views import DoYouKnow
from neo4j_connect import Relationships

intents = discord.Intents.default()
intents.members = True

description = '''
A bot that tracks the relationship of people in a discord.

It does this by asking each user who joins a simple question:

Who do you know?

The user they are claimed to know is then sent a message asking, 'Do you know ___?'

If so, 
'''

class SnowflakeWrapper(Snowflake):
    def __init__(self, snowflake: int):
        self.id = snowflake


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

    @tasks.loop(seconds=10)
    async def process_update_center_requests(self):
        await self.wait_until_ready()

        guild_manager = postgres_connect.GuildManager()
        transaction_manager = postgres_connect.TransactionsManager()
        relationships = neo4j_connect.Relationships()

        # We should never end terminate this.
        oldest_center = transaction_manager.get_oldest_transaction()

        if not oldest_center:
            return

        related_roles_and_guilds = guild_manager.get_center(oldest_center)

        relationships.find_centers_about(oldest_center)
        # TODO: This should all be batched.
        for role_snowflake, guild_snowflake in related_roles_and_guilds:
            updatables = relationships.knowers_within(oldest_center, 3)

            for updatable in updatables:
                current_guild = await self.fetch_guild(guild_snowflake)
                if not current_guild:
                    logging.info(f"Discord guild {guild_snowflake} not found in process updates.")

                role = await current_guild.fetch_role(role_snowflake)

                if not role:
                    logging.info(f"Discord role {role_snowflake} not found in process updates.")

                member = await current_guild.fetch_member(updatable)

                if not member:
                    logging.info(f"Discord user {updatable} in {guild_snowflake} not found in process updates.")
                await member.add_roles(role)

        transaction_manager.remove_transaction(oldest_center)

client = DunbarClient(intents=intents)


@client.tree.command(
    name='iknow',
    description='Note that you know this user'
)
@discord.app_commands.describe(member="Member to mark as known by you.")
async def iknow(interaction: discord.Interaction, member: discord.Member):
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

    await interaction.response.send_message(f'{member} marked as known by you.', ephemeral=True)
    # Ask the knowee if they know the requester, establishing friendship.
    await dm_confirm_knowership(requester_snowflake, knowee_snowflake,interaction.guild)

@client.tree.command(
    name='add_center',
    description='Add a user to be the center node for the role to be applied'
)
@discord.app_commands.describe(member="Member to be the center")
@discord.app_commands.describe(role="Role to be applied to members who have friendship with N steps of the member.")
@app_commands.checks.has_permissions(administrator=True) # Without this malicious users could execute this command to include themselves, thus bypassing this check.
async def add_center(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    guild_manager = postgres_connect.GuildManager()
    transaction_manager = postgres_connect.TransactionsManager()
    relationships = neo4j_connect.Relationships()
    relationships.add_center_tag(member.id)
    if guild_manager.get_specific_center(interaction.guild.id, member.id):
        # The entry exists, we just need to modify it
        guild_manager.change_guild_role(interaction.guild.id, member.id, role.id)
        await interaction.response.send_message(f'Role for friendship with member is now {role.name}')
    else:
        guild_manager.create_guild_relationship(interaction.guild.id, member.id, role.id)
        transaction_manager.create_transaction(member.id)
        await interaction.response.send_message(f'A new center ({member.name}) for this guild has been added with {role.name}')

@client.tree.command(
    name='force_update_about_user',
    description='Adds transactions for the centers about a user to be updated.'
)
@discord.app_commands.describe(member="Member to force updates about")
@app_commands.checks.has_permissions(administrator=True) # Without this malicious users could execute this command to include themselves, thus bypassing this check.
async def force_update_about_user(interaction: discord.Interaction, member: discord.Member):
    transaction_manager = postgres_connect.TransactionsManager()

    relations = Relationships()
    centers = relations.find_centers_about(member.id)

    for center in centers:
        transaction_manager.create_transaction(center)

    if not centers:
        await interaction.response.send_message(f'No centers found about {member.name}.', ephemeral=True)
    else:
        out = table2ascii.table2ascii(
            header = ["Center"],
            body = [centers],
            style = PresetStyle.thin_compact
        )
        await interaction.response.send_message(f'A new transaction has been created for centers about {member.name}. See logs for helper thread.\n```\n{out}```\n', ephemeral=True)




@client.tree.command(
    name='get_centers',
    description='Get the centers and roles currently configured for this guild'
)
async def get_current_centers(interaction: discord.Interaction):
    guild_manager = postgres_connect.GuildManager()
    centers = guild_manager.get_related_centers(interaction.guild.id)

    parsed = []

    for entry in centers:
        center = await interaction.guild.fetch_member(entry[0])
        role = await interaction.guild.fetch_role(entry[1])

        parsed.append([center.name, role.name])


    out = table2ascii.table2ascii(
        header = ["Center", "Role"],
        body = parsed,
        style = PresetStyle.thin_compact
    )

    await interaction.response.send_message(f"```\n{out}```\n", ephemeral=True)

@client.tree.command(
    name='knowers_within',
    description='List users who know a node within X jumps of you that also knows you.'
)
@discord.app_commands.describe(jumps='The maximum number of KNOWS hops to explore from you (1-5 recommended).')
async def knowers_within(interaction: discord.Interaction, jumps: int):
    relationships = neo4j_connect.Relationships()

    origin = interaction.user.id

    # Ensure the origin exists in the graph for consistent querying
    if not relationships.does_snowflake_exists(origin):
        await interaction.response.send_message('You do not appear to be within the database. Try making some friends first!', ephemeral=True)

    try:
        jumps = int(jumps)
        if jumps < 1:
            await interaction.response.send_message('jumps must be >= 1', ephemeral=True)
            return
    except Exception:
        await interaction.response.send_message('Invalid jumps value', ephemeral=True)
        return

    snowflakes = relationships.knowers_within(origin, jumps)

    names = []
    for sf in snowflakes:
        try:
            member = await interaction.guild.fetch_member(int(sf))
            names.append(member.display_name)
        except Exception:
            names.append(str(sf))

    if not names:
        await interaction.response.send_message('No matching users found.', ephemeral=True)
        return

    # Build a simple ASCII table
    body = [[name] for name in sorted(names, key=str.lower)]
    out = table2ascii.table2ascii(
        header=["Users"],
        body=body,
        style=PresetStyle.thin_compact
    )

    await interaction.response.send_message(f"```\n{out}```", ephemeral=True)

async def dm_confirm_knowership(requester_snowflake, target_snowflake, guild: Guild):
    # We assume that the users already exist, because they would be created by the iknow command
    # additionally we fetch them by guild so that we can apply the necessary role.
    requester = await guild.fetch_member(requester_snowflake)
    target = await guild.fetch_member(target_snowflake)

    guild_manager = postgres_connect.GuildManager()
    centers = guild_manager.get_related_centers(guild.id)

    role_instance = guild.get_role(known_role.id)
    center_instance = guild.get_member(center_user.id)

    await target.send(content=f"Do you know {requester.display_name}?", view=DoYouKnow(requester, target, role_instance, center_instance))


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

    if not client.process_update_center_requests.is_running():
        client.process_update_center_requests.start()

if __name__ == '__main__':
    # Load in .env file
    load_dotenv()
    client.run(os.getenv('DISCORD_TOKEN'))