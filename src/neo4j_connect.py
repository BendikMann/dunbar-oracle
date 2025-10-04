import neo4j
from neo4j import GraphDatabase


class Relationships:
    def __init__(self, driver=None):
        # TODO: Implement env variable for both localhost and auth
        self.driver = driver if driver is not None else GraphDatabase.driver("neo4j://localhost:7687", auth=None)
        # Name of the database we are operating on.
        self.database = "neo4j"

    def close(self):
        self.driver.close()

    def add_knowership(self, snowflake, friend_snowflake):
        with self.driver.session() as session:
            # TODO: We should check before we add the user because it is possible to add this relationship many times.
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
            result = session.run("MATCH (this:User {snowflake: $this}), (them:User {snowflake: $them})" +
                                 "MATCH this_to_them = SHORTEST 1 (this)-[:KNOWS]->+(them)" +
                                 "MATCH them_to_this = SHORTEST 1 (them)-[:KNOWS]->+(this)" +
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

    def friends_about(self, center) -> set[str]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (this:User {snowflake: $snowflake})
                // mutual 1-hop neighbors
                MATCH (this)-[:KNOWS]-(m1:User)
                WHERE EXISTS { MATCH (this)-[:KNOWS]->(m1) } AND EXISTS { MATCH (m1)-[:KNOWS]->(this) }
                WITH this, collect(DISTINCT m1) AS N1
                // mutual 2-hop neighbors via mutual intermediary
                UNWIND N1 AS m
                MATCH (m)-[:KNOWS]-(n2:User)
                WHERE EXISTS { MATCH (m)-[:KNOWS]->(n2) } AND EXISTS { MATCH (n2)-[:KNOWS]->(m) }
                WITH this, N1, collect(DISTINCT n2.snowflake) AS S2
                WITH [x IN N1 | x.snowflake] AS S1, S2, this.snowflake AS me
                WITH S1 + S2 + [me] AS s
                UNWIND s AS sf
                RETURN DISTINCT sf AS snowflake
                """,
                snowflake=center,
            )
            output = result.values()
            unwrapped = [item[0] for item in output]
            lengths = set(unwrapped)
            return lengths

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

    def add_center_tag(self, snowflake):
        with self.driver.session() as session:
            _ = session.run("MATCH (n {snowflake: $snowflake}) SET n.center = true", snowflake=snowflake)

    def remove_center_tag(self, snowflake):
        with self.driver.session() as session:
            _ = session.run("MATCH (n {snowflake: $snowflake}) REMOVE n.center", snowflake=snowflake)

    def find_centers_about(self, snowflake, distance=3):
        """
        Return center-tagged users who mutually know a node within 1..distance hops of the origin, where:
        - The path from origin to the intermediate node is mutually reciprocated at every step.
        - The center candidate mutually knows the intermediate node OR is the intermediate node itself if it is tagged center.
        - The origin is excluded from results.
        Note: Distance applies to the origin->intermediate path only; the final mutual hop to the center is not counted.
        """
        # Ensure a sane, bounded traversal depth (avoid unbounded *1.. which is very slow)
        try:
            depth_int = int(distance)
        except Exception:
            depth_int = 3
        if depth_int < 1:
            depth_int = 1
        query = f"""
                MATCH (o:User {{snowflake: $origin}})
                MATCH p = (o)-[:KNOWS*1..{depth_int}]->(n:User)
                WHERE all(i IN range(0, size(nodes(p)) - 2) WHERE EXISTS {{
                    MATCH (x)-[:KNOWS]->(y)
                    WHERE x = nodes(p)[i+1] AND y = nodes(p)[i]
                  }})
                WITH DISTINCT o, n
                CALL {{
                  WITH o, n
                  // Case 1: the intermediate node itself is a center
                  WITH o, n
                  WHERE coalesce(n.center, false) = true
                  RETURN n AS cand
                  UNION
                  // Case 2: any center mutually connected to the intermediate node
                  WITH o, n
                  MATCH (c:User)-[:KNOWS]->(n)
                  WHERE EXISTS {{ MATCH (n)-[:KNOWS]->(c) }} AND coalesce(c.center, false) = true
                  RETURN c AS cand
                }}
                WITH DISTINCT o, cand
                WHERE cand <> o
                RETURN DISTINCT cand.snowflake AS snowflake
                """
        with self.driver.session() as session:
            result = session.run(query, origin=snowflake)
            values = result.values()
            return [v[0] for v in values]

    def knowers_within(self, origin_snowflake, max_depth: int) -> set[str]:
        """
        Returns the set of snowflakes K such that there exists a node N within 1..max_depth KNOWS hops from origin O
        where N KNOWS O, and K KNOWS N. The origin is excluded from the result.
        """
        # Bound traversal to avoid unbounded expansion; effective bound mirrors prior semantics.
        try:
            d = int(max_depth)
        except Exception:
            d = 1
        bound = 1 if d == 1 else max(1, d - 1)
        query = f"""
                MATCH (o:User {{snowflake: $origin}})
                MATCH p = (o)-[:KNOWS*1..{bound}]->(n:User)
                WHERE all(i IN range(0, size(nodes(p)) - 2) WHERE EXISTS {{
                    MATCH (x)-[:KNOWS]->(y)
                    WHERE x = nodes(p)[i+1] AND y = nodes(p)[i]
                  }})
                WITH DISTINCT o, n
                MATCH (k:User)-[:KNOWS]->(n)
                WHERE k <> o AND EXISTS {{ MATCH (n)-[:KNOWS]->(k) }}
                RETURN DISTINCT k.snowflake AS snowflake
                """
        with self.driver.session() as session:
            result = session.run(query, origin=origin_snowflake)
            values = result.values()
            return set(v[0] for v in values)
