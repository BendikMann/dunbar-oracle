CREATE TABLE Centers
(
    UserSnowflake   BIGINT,
    GuildSnowflake  BIGINT,
    RoleSnowflake   BIGINT,
    Radius          INT DEFAULT 3,
    CreationTime    TIMESTAMP default CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_and_guild PRIMARY KEY (UserSnowflake, GuildSnowflake)
);