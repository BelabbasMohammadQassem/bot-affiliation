from src.bot import AmazonAffiliateBot
from dotenv import load_dotenv
import os
import discord

def main():
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        raise ValueError("Le token Discord n'est pas défini dans le fichier .env")
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = AmazonAffiliateBot(
        command_prefix="!",
        intents=intents,
        disable_audio=True
    )
    bot.run(token)

if __name__ == "__main__":
    main()
