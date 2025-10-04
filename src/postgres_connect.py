from typing import Union

import psycopg


class TransactionsManager:
    """
    Transaction Manager handles the Update table which determines which centers need to be recomputed.
    """
    def __init__(self):
        self.dbname = "postgres"
        self.user = "postgres"
        self.password = "root"
        self.con_string = f"dbname={self.dbname} user={self.user} password={self.password}"

    def create_transaction(self, center_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO Updates (CenterSnowflake) VALUES (%s)", (center_snowflake,)
                )

    def get_oldest_transaction(self):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM Updates ORDER BY CreationTime LIMIT 1",
                )
                # return the first result (which should only ever be one or zero) and give the first element (which should always be snowflake)
                result = cursor.fetchall()

                if len(result) > 0:
                    return result[0][1]
        return None

    def remove_transaction(self, center_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM Updates WHERE CenterSnowflake = %s", (center_snowflake,)
                )


class GuildManager:
    def __init__(self):
        self.dbname = "postgres"
        self.user = "postgres"
        self.password = "root"
        self.con_string = f"dbname={self.dbname} user={self.user} password={self.password}"

    def create_guild_relationship(self, guild_snowflake, center_snowflake, role_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                 "INSERT INTO centers (usersnowflake, guildsnowflake, rolesnowflake) VALUES (%s, %s, %s)", (center_snowflake, guild_snowflake, role_snowflake)
            )

            conn.commit()

    def change_guild_role(self, guild_snowflake, center_snowflake, role_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE centers SET rolesnowflake = %s WHERE usersnowflake = %s AND guildsnowflake = %s", (role_snowflake, center_snowflake, guild_snowflake))


    def remove_guild_relationship(self, guild_snowflake, center_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM centers WHERE usersnowflake = %s AND guildsnowflake = %s", (center_snowflake, guild_snowflake))

    def get_related_centers(self, guild_snowflake) -> Union[ list[list[int, int]]]:
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT usersnowflake, rolesnowflake FROM centers WHERE guildsnowflake = %s", (guild_snowflake,))

                centers = cursor.fetchall()

                return centers if centers else []

    def get_specific_center(self, guild_snowflake, center_snowflake) -> Union[int, None]:
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT rolesnowflake FROM centers WHERE guildsnowflake = %s AND usersnowflake = %s", (guild_snowflake, center_snowflake))

                # By definition this must be one, guildsnowflake and usersnowflake make the primary key of rolesnowflake
                center = cursor.fetchall()

                return center[0][0] if center else None

    def get_center(self, center_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT rolesnowflake, guildsnowflake FROM centers WHERE usersnowflake = %s",
                               (center_snowflake,))
                centers = cursor.fetchall()

                return centers if centers else None