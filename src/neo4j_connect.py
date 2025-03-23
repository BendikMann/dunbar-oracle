import neo4j
from neo4j import GraphDatabase


class Relationships:
    def __init__(self):
        # TODO: Implement env variable for both localhost and auth
        self.driver = GraphDatabase.driver("neo4j://localhost:7687", auth=None)
        # Name of the database we are operating on.
        self.database = "neo4j"

    def close(self):
        self.driver.close()

    def add_knowership(self, snowflake, friend_snowflake):
        with self.driver.session() as session:
            result = session.run("MATCH (knower:User {snowflake: $snowflake}), (knowee:User {snowflake: $friend_snowflake})" +
                                      "CREATE (knower)-[:KNOWS]->(knowee)",
                                      snowflake=snowflake,
                                      friend_snowflake=friend_snowflake)
            result.consume()


    def does_snowflake_know(self, snowflake, suspect_snowflake):
        with (self.driver.session() as session):
            result = session.run("MATCH (knower:User {snowflake: $snowflake}), (knowee:User {snowflake: $suspect_snowflake}) " +
                                      "RETURN EXISTS ((knower)-[:KNOWS]->(knowee)) AS Predicate",
                                             snowflake=snowflake,
                                             suspect_snowflake=suspect_snowflake
                                            )
            if result.data():
                return True
            else:
                return False


    def are_snowflake_friends(self, this, them):
        with self.driver.session() as session:
            result = session.run("MATCH (this:User {snowflake: $this}), (them:User {snowflake: $them})\n" +
                                      "RETURN EXISTS {\n" +
                                      "MATCH (this)-[:KNOWS]->(that)\n" +
                                      "UNION\n" +
                                      "MATCH (that)-[:KNOWS]->(this)\n" +
                                      "} AS areFriends",
                                             this=this,
                                             them=them
                                            )
            if result.data():
                return True
            else:
                return False


    def snowflake_affiliation(self, this, them) -> int:
        with self.driver.session() as session:
            result = session.run("MATCH (this:User {snowflake: $this}), (them:User {snowflake: $them})\n" +
                                 "MATCH this_to_them = SHORTEST 1 (this)-[:KNOWS]->+(them)\n" +
                                 "MATCH them_to_this = SHORTEST 1 (them)-[:KNOWS]->+(this)\n" +
                                 "RETURN length(this_to_them) AS this_affiliation, length(them_to_this) AS them_affiliation",
                                 this=this,
                                 them=them)

            lengths = result.values()

            if lengths:
                actual_lengths = lengths[0]
                this_length = actual_lengths[0]
                them_length = actual_lengths[1]

                min_length = min(this_length, them_length)

                return min_length



            return 0
    def create_user(self, snowflake):
        with (self.driver.session() as session):
            session.run("CREATE (:User {snowflake: $snowflake})",
                        snowflake=snowflake
                        )
    def does_snowflake_exists(self, snowflake):
        with self.driver.session() as session:
            result = session.run("MATCH (n) WHERE n.snowflake = $this RETURN COUNT(n) > 0 as SnowflakeExists",
                                 this=snowflake)

            return result.value()[0]