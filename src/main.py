import os

from dotenv import load_dotenv

import bot
import logging


if __name__ == '__main__':
    # It may be provided
    load_dotenv()



    logging.getLogger().addHandler(logging.StreamHandler())

    discord_token = os.getenv('DISCORD_TOKEN')


    if not discord_token:
        logging.warning(f"Discord Token is not in ENV variable, checking runs/secret/discord_token")
        with open(os.getenv('DISCORD_TOKEN_FILE'), 'r') as secret:
            discord_token = secret.read()
    else:
        logging.info(f"Discord Token found in ENV")

    bot.client.run(discord_token)