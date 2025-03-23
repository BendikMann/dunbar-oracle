import string
import unittest
import random

import neo4j_connect


def random_char(y):
    return ''.join(random.choice(string.ascii_letters) for _ in range(y))

class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.database = neo4j_connect.Relationships()

    def tearDown(self):
        self.database.close()

    def test_create_user(self):
        snowflake = random_char(20)
        self.database.create_user(snowflake)

    def test_does_user_exist_and_user_exists(self):
        snowflake = random_char(20)
        self.database.create_user(snowflake)

        ret = self.database.does_snowflake_exists(snowflake)
        self.assertTrue(ret)

    def test_does_user_exist_and_user_doesnt_exists(self):
        snowflake = random_char(20)
        ret = self.database.does_snowflake_exists(snowflake)
        self.assertFalse(ret)


    def test_create_knowership(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)

        self.database.create_user(snowflake1)
        self.database.create_user(snowflake2)

        self.database.add_knowership(snowflake1, snowflake2)

    def test_knowership(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)
        snowflake3 = random_char(20)
        self.database.create_user(snowflake1)
        self.database.create_user(snowflake2)

        self.database.add_knowership(snowflake1, snowflake2)
        self.assertTrue(self.database.does_snowflake_know(snowflake1, snowflake2))
        self.assertFalse(self.database.does_snowflake_know(snowflake1, snowflake3))

    def test_friendship(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)
        snowflake3 = random_char(20)

        self.database.create_user(snowflake1)
        self.database.create_user(snowflake2)
        # make 1 and 2 friends
        self.database.add_knowership(snowflake1, snowflake2)
        self.database.add_knowership(snowflake2, snowflake1)
        # make 1 and 3 just know each other
        self.database.add_knowership(snowflake1, snowflake3)

        # snowflakes are friends if they both 'know' each other.
        are_friends = self.database.are_snowflake_friends(snowflake1, snowflake2)
        self.assertTrue(are_friends)
        # If snowflake1 and snowflake2 are friends, so should snowflake2 and snowflake1
        are_friends_idempotent = self.database.are_snowflake_friends(snowflake2, snowflake1)
        self.assertTrue(are_friends_idempotent)


        not_friends = self.database.are_snowflake_friends(snowflake1, snowflake3)
        self.assertFalse(not_friends)
        not_friends_idempotent = self.database.are_snowflake_friends(snowflake3, snowflake1)
        self.assertFalse(not_friends_idempotent)

        not_friends = self.database.are_snowflake_friends(snowflake2, snowflake3)
        self.assertFalse(not_friends)
        not_friends_idempotent = self.database.are_snowflake_friends(snowflake3, snowflake2)
        self.assertFalse(not_friends_idempotent)

    def test_association_traversal(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)
        snowflake3 = random_char(20)

        self.database.create_user(snowflake1)
        self.database.create_user(snowflake2)
        self.database.create_user(snowflake3)

        self.database.add_knowership(snowflake1, snowflake2)
        self.database.add_knowership(snowflake2, snowflake1)

        self.database.add_knowership(snowflake2, snowflake3)
        self.database.add_knowership(snowflake3, snowflake2)


        s1_to_s2 = self.database.snowflake_affiliation(snowflake1, snowflake2)
        s2_to_s1 = self.database.snowflake_affiliation(snowflake2, snowflake1)
        self.assertEqual(s1_to_s2, s2_to_s1)
        self.assertEqual(s2_to_s1, 1)

        s2_to_s3 = self.database.snowflake_affiliation(snowflake2, snowflake3)
        s3_to_s2 = self.database.snowflake_affiliation(snowflake3, snowflake2)
        self.assertEqual(s2_to_s3, s3_to_s2)
        self.assertEqual(s2_to_s3, 1)


        s1_to_s3 = self.database.snowflake_affiliation(snowflake1, snowflake3)
        s3_to_s1 = self.database.snowflake_affiliation(snowflake3, snowflake1)
        self.assertEqual(s1_to_s3, s3_to_s1)
        self.assertEqual(2, s1_to_s3)





if __name__ == '__main__':
    unittest.main()
