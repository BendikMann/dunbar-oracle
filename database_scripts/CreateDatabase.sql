CREATE TABLE Centers
(
    UserSnowflake   BIGINT not null,
    GuildSnowflake  BIGINT not null,
    RoleSnowflake   BIGINT,
    Radius          INT DEFAULT 3 not null,
    CreationTime    TIMESTAMP default CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_and_guild PRIMARY KEY (UserSnowflake, GuildSnowflake)
);

CREATE TABLE Updates
(
    transaction_id serial primary key,
    CenterSnowflake BIGINT UNIQUE not null,
    CreationTime    TIMESTAMP default CURRENT_TIMESTAMP
);