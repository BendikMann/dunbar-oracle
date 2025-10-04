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


    def test_add_centership(self):
        snowflake1 = random_char(20)
        self.database.create_user(snowflake1)
        self.database.add_center_tag(snowflake1)

    def test_remove_centership(self):
        snowflake1 = random_char(20)
        self.database.create_user(snowflake1)
        self.database.add_center_tag(snowflake1)
        self.database.remove_center_tag(snowflake1)

    def test_get_centers(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)
        snowflake3 = random_char(20)

        self.database.create_user(snowflake1)
        self.database.create_user(snowflake2)
        self.database.create_user(snowflake3)

        self.database.add_center_tag(snowflake1)
        self.database.add_center_tag(snowflake2)

        self.database.add_knowership(snowflake1, snowflake2)
        self.database.add_knowership(snowflake2, snowflake1)

        self.database.add_knowership(snowflake1, snowflake3)
        self.database.add_knowership(snowflake3, snowflake1)

        centers = self.database.find_centers_about(snowflake1, 1)
        # New semantics: exclude origin, only include center-tagged users who mutually know
        # a node within depth that knows back to origin. Here, snowflake2 qualifies via snowflake2 itself.
        self.assertNotIn(snowflake1, centers)
        self.assertIn(snowflake2, centers)

    def test_knowers_within(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)
        snowflake3 = random_char(20)
        snowflake4 = random_char(20)
        snowflake5 = random_char(20)
        snowflake6 = random_char(20)

        # create users
        for sf in [snowflake1, snowflake2, snowflake3, snowflake4, snowflake5, snowflake6]:
            self.database.create_user(sf)

        # relationships
        # snowflake1 <-> snowflake2 (mutual)
        self.database.add_knowership(snowflake1, snowflake2)
        self.database.add_knowership(snowflake2, snowflake1)
        # snowflake1 -> snowflake3 (not mutual with origin)
        self.database.add_knowership(snowflake1, snowflake3)
        # knowers must be mutual with the intermediate node and that node must know back to origin
        # snowflake4 <-> snowflake2 (qualifies)
        self.database.add_knowership(snowflake4, snowflake2)
        self.database.add_knowership(snowflake2, snowflake4)
        # snowflake5 <-> snowflake3 (does NOT qualify because snowflake3 does not know snowflake1)
        self.database.add_knowership(snowflake5, snowflake3)
        self.database.add_knowership(snowflake3, snowflake5)
        # snowflake6 <-> snowflake2 (qualifies)
        self.database.add_knowership(snowflake6, snowflake2)
        self.database.add_knowership(snowflake2, snowflake6)

        result = self.database.knowers_within(snowflake1, 1)

        self.assertIn(snowflake4, result)
        self.assertIn(snowflake6, result)
        self.assertNotIn(snowflake5, result)
        self.assertNotIn(snowflake1, result)

    def test_knowers_dont_expand_too_far(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)
        snowflake3 = random_char(20)
        snowflake4 = random_char(20)
        snowflake5 = random_char(20)
        snowflake6 = random_char(20)

        # create users
        for sf in [snowflake1, snowflake2, snowflake3, snowflake4, snowflake5, snowflake6]:
            self.database.create_user(sf)

        # relationships
        self.database.add_knowership(snowflake1, snowflake2)
        self.database.add_knowership(snowflake2, snowflake1)

        self.database.add_knowership(snowflake2, snowflake3)
        self.database.add_knowership(snowflake3, snowflake2)

        self.database.add_knowership(snowflake3, snowflake4)
        self.database.add_knowership(snowflake4, snowflake3)

        self.database.add_knowership(snowflake4, snowflake5)
        self.database.add_knowership(snowflake5, snowflake4)

        result = self.database.knowers_within(snowflake1, 1)

        self.assertIn(snowflake3, result)
        self.assertNotIn(snowflake4, result)
        self.assertNotIn(snowflake5, result)

    def test_knowers_dont_expand_too_far_length2(self):
        snowflake1 = random_char(20)
        snowflake2 = random_char(20)
        snowflake3 = random_char(20)
        snowflake4 = random_char(20)
        snowflake5 = random_char(20)
        snowflake6 = random_char(20)

        # create users
        for sf in [snowflake1, snowflake2, snowflake3, snowflake4, snowflake5, snowflake6]:
            self.database.create_user(sf)

        # relationships
        self.database.add_knowership(snowflake1, snowflake2)
        self.database.add_knowership(snowflake2, snowflake1)

        self.database.add_knowership(snowflake2, snowflake3)
        self.database.add_knowership(snowflake3, snowflake2)

        self.database.add_knowership(snowflake3, snowflake4)
        self.database.add_knowership(snowflake4, snowflake3)

        self.database.add_knowership(snowflake4, snowflake5)
        self.database.add_knowership(snowflake5, snowflake4)

        result = self.database.knowers_within(snowflake1, 3)

        self.assertIn(snowflake3, result)
        self.assertIn(snowflake4, result)
        self.assertNotIn(snowflake5, result)

    def test_centers_within_depth1(self):
        o = random_char(20)
        a = random_char(20)
        b = random_char(20)
        c1 = random_char(20)
        c2 = random_char(20)
        cbad = random_char(20)
        non_center = random_char(20)

        for sf in [o, a, b, c1, c2, cbad, non_center]:
            self.database.create_user(sf)

        # origin mutual with a; b is not mutual with origin
        self.database.add_knowership(o, a)
        self.database.add_knowership(a, o)
        self.database.add_knowership(o, b)

        # centers
        self.database.add_center_tag(c1)
        self.database.add_center_tag(c2)
        self.database.add_center_tag(cbad)
        # non-center should be ignored even if connected
        # mutual with a
        self.database.add_knowership(c1, a)
        self.database.add_knowership(a, c1)
        self.database.add_knowership(c2, a)
        self.database.add_knowership(a, c2)
        # connected to b only (b does not know origin)
        self.database.add_knowership(cbad, b)
        self.database.add_knowership(b, cbad)
        # non-center mutual with a
        self.database.add_knowership(non_center, a)
        self.database.add_knowership(a, non_center)

        res = self.database.find_centers_about(o, 1)
        self.assertIn(c1, res)
        self.assertIn(c2, res)
        self.assertNotIn(cbad, res)
        self.assertNotIn(non_center, res)
        self.assertNotIn(o, res)

    def test_centers_excludes_origin(self):
        o = random_char(20)
        a = random_char(20)
        c1 = random_char(20)
        for sf in [o, a, c1]:
            self.database.create_user(sf)
        self.database.add_center_tag(o)
        self.database.add_center_tag(c1)
        # mutual origin<->a
        self.database.add_knowership(o, a)
        self.database.add_knowership(a, o)
        # center c1 mutual with a
        self.database.add_knowership(c1, a)
        self.database.add_knowership(a, c1)
        res = self.database.find_centers_about(o, 1)
        self.assertIn(c1, res)
        self.assertNotIn(o, res)

    def test_centers_respect_depth_limits(self):
        o = random_char(20)
        a = random_char(20)
        b = random_char(20)
        c_near = random_char(20)
        c_deep = random_char(20)
        for sf in [o, a, b, c_near, c_deep]:
            self.database.create_user(sf)
        self.database.add_center_tag(c_near)
        self.database.add_center_tag(c_deep)
        # chain: o <-> a <-> b
        self.database.add_knowership(o, a)
        self.database.add_knowership(a, o)
        self.database.add_knowership(a, b)
        self.database.add_knowership(b, a)
        # centers connect
        self.database.add_knowership(c_near, a)
        self.database.add_knowership(a, c_near)
        self.database.add_knowership(c_deep, b)
        self.database.add_knowership(b, c_deep)
        res1 = self.database.find_centers_about(o, 1)
        self.assertIn(c_near, res1)
        self.assertNotIn(c_deep, res1)
        res2 = self.database.find_centers_about(o, 2)
        self.assertIn(c_near, res2)
        self.assertIn(c_deep, res2)

    def test_centers_require_mutual_chain(self):
        o = random_char(20)
        a = random_char(20)
        c1 = random_char(20)
        for sf in [o, a, c1]:
            self.database.create_user(sf)
        self.database.add_center_tag(c1)
        # non-mutual: o -> a only
        self.database.add_knowership(o, a)
        # center connected to a mutually
        self.database.add_knowership(c1, a)
        self.database.add_knowership(a, c1)
        res = self.database.find_centers_about(o, 1)
        self.assertNotIn(c1, res)


if __name__ == '__main__':
    unittest.main()
