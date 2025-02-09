from src.bot import AmazonAffiliateBot
from dotenv import load_dotenv
import os

def main():
    # Charge les variables d'environnement
    load_dotenv()
    
    # Récupère le token Discord
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        raise ValueError("Le token Discord n'est pas défini dans le fichier .env")
    
    # Crée et lance le bot
    bot = AmazonAffiliateBot()
    bot.run(token)

if __name__ == "__main__":
    main()
