from src.bot import AmazonAffiliateBot
from dotenv import load_dotenv
import os
import discord

def main():
    # Charge les variables d'environnement
    load_dotenv()
    
    # Récupère le token Discord
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        raise ValueError("Le token Discord n'est pas défini dans le fichier .env")
    
    # Configuration des intents et désactivation de l'audio
    intents = discord.Intents.default()
    intents.message_content = True
    
    # Crée et lance le bot avec l'audio désactivé
    bot = AmazonAffiliateBot(intents=intents, disable_audio=True)
    bot.run(token)

if __name__ == "__main__":
    main()
