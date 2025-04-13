import string
import unittest
import random

import postgres_connect


def random_char(y):
    return ''.join(random.choice(string.ascii_letters) for _ in range(y))


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.database = postgres_connect.GuildManager()

    def test_create_guild_relationship(self):
        guild_snowflake = random.randint(0, 1_000_000_000_000)
        center_snowflake = random.randint(0, 1_000_000_000_000)
        role_snowflake = random.randint(0, 1_000_000_000_000)

        self.database.create_guild_relationship(guild_snowflake, center_snowflake, role_snowflake)

    def test_get_guild_relationships_single(self):
        guild_snowflake = random.randint(0, 1_000_000_000_000)
        center_snowflake = random.randint(0, 1_000_000_000_000)
        role_snowflake = random.randint(0, 1_000_000_000_000)

        self.database.create_guild_relationship(guild_snowflake, center_snowflake, role_snowflake)
        ret = self.database.get_related_centers(guild_snowflake)

        self.assertEqual(ret[0][0], center_snowflake)
        self.assertEqual(ret[0][1], role_snowflake)


    def test_get_guild_relationships_multiple(self):
        guild_snowflake = random.randint(0, 1_000_000_000_000)
        center_snowflake = random.randint(0, 1_000_000_000_000)
        role_snowflake = random.randint(0, 1_000_000_000_000)

        center2_snowflake = random.randint(0, 1_000_000_000_000)
        role2_snowflake = random.randint(0, 1_000_000_000_000)

        self.database.create_guild_relationship(guild_snowflake, center_snowflake, role_snowflake)
        self.database.create_guild_relationship(guild_snowflake, center2_snowflake, role2_snowflake)

        ret = self.database.get_related_centers(guild_snowflake)
        # It is possible
        self.assertEqual(ret[0][0], center_snowflake)
        self.assertEqual(ret[1][0], center2_snowflake)
        self.assertEqual(ret[0][1], role_snowflake)
        self.assertEqual(ret[1][1], role2_snowflake)

    def test_get_specific_guild_relationships(self):
        guild_snowflake = random.randint(0, 1_000_000_000_000)
        center_snowflake = random.randint(0, 1_000_000_000_000)
        role_snowflake = random.randint(0, 1_000_000_000_000)

        center2_snowflake = random.randint(0, 1_000_000_000_000)
        role2_snowflake = random.randint(0, 1_000_000_000_000)

        self.database.create_guild_relationship(guild_snowflake, center_snowflake, role_snowflake)
        self.database.create_guild_relationship(guild_snowflake, center2_snowflake, role2_snowflake)

        ex1 = self.database.get_specific_center(guild_snowflake, center_snowflake)
        ex2 = self.database.get_specific_center(guild_snowflake, center2_snowflake)
        self.assertEqual(ex1, role_snowflake)
        self.assertEqual(ex2, role2_snowflake)

    def test_delete_guild_relationship(self):
        guild_snowflake = random.randint(0, 1_000_000_000_000)
        center_snowflake = random.randint(0, 1_000_000_000_000)
        role_snowflake = random.randint(0, 1_000_000_000_000)

        self.database.create_guild_relationship(guild_snowflake, center_snowflake, role_snowflake)
        self.assertTrue(self.database.get_related_centers(guild_snowflake))
        self.database.remove_guild_relationship(guild_snowflake, center_snowflake)
        self.assertFalse(self.database.get_related_centers(guild_snowflake))

    def test_modify_guild_relationship(self):
        guild_snowflake = random.randint(0, 1_000_000_000_000)
        center_snowflake = random.randint(0, 1_000_000_000_000)
        role_snowflake = random.randint(0, 1_000_000_000_000)

        self.database.create_guild_relationship(guild_snowflake, center_snowflake, role_snowflake)

        new_role_snowflake = random.randint(0, 1_000_000_000_000)
        self.database.change_guild_role(guild_snowflake, center_snowflake, new_role_snowflake)
        related = self.database.get_related_centers(guild_snowflake)
        role = related[0][1]
        self.assertEqual(new_role_snowflake, role)


