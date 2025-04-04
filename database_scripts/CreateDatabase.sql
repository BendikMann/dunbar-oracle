CREATE TABLE Centers
(
    UserSnowflake   INT,
    GuildSnowflake  INT PRIMARY KEY,
    RoleSnowflake   INT,
    Radius          INT DEFAULT 3,
    CreationTime    TIMESTAMP default CURRENT_TIMESTAMP
);

ALTER TABLE Centers
ADD CONSTRAINT unique_user_and_guild UNIQUE (UserSnowflake, GuildSnowflake);