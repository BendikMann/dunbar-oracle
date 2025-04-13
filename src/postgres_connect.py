import psycopg


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

    def get_related_centers(self, guild_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT usersnowflake, rolesnowflake FROM centers WHERE guildsnowflake = %s", (guild_snowflake,))

                centers = cursor.fetchall()

                return centers

    def get_specific_center(self, guild_snowflake, center_snowflake):
        with psycopg.connect(self.con_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT rolesnowflake FROM centers WHERE guildsnowflake = %s AND usersnowflake = %s", (guild_snowflake, center_snowflake))

                # By definition this must be one, guildsnowflake and usersnowflake make the primary key of rolesnowflake
                center = cursor.fetchall()
                return center[0][0]