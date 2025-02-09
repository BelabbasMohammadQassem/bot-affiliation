import discord
from discord.ext import commands
import re
import requests
import pyshorteners
import os
from urllib.parse import urlparse, parse_qs

class AmazonAffiliateBot(commands.Bot):
    def __init__(self, **kwargs):
        # Suppression de la double initialisation
        super().__init__(**kwargs)
        
        self.affiliate_tag = os.getenv('AFFILIATE_TAG')
        self.shortener = pyshorteners.Shortener()

    async def setup_hook(self):
        print("Bot is setting up...")

    def extract_amazon_url(self, content):
        patterns = [
            r'https?://(?:www\.)?amazon\.(?:com|fr|co\.uk|de|it|es)/[^\s]+',
            r'https?://amzn\.(?:to|eu)/[^\s]+',
            r'https?://a\.co/d/[^\s]+',
            r'https?://(?:www\.)?amazon\.(?:com|fr|co\.uk|de|it|es)/(?:dp|gp/product)/[A-Z0-9]+/?[^\s]*'
        ]
            
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                return match.group(0)
        return None

    def unshorten_url(self, url):
        try:
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            response = session.get(url, headers=headers, allow_redirects=True, timeout=10)
            final_url = response.url
            print(f"URL finale après déroulage : {final_url}")
            return final_url
        except Exception as e:
            print(f"Erreur lors du déroulage de l'URL : {e}")
            return url

    def clean_amazon_url(self, url):
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        product_id = None
        
        for i, part in enumerate(path_parts):
            if part in ['dp', 'gp', 'product', 'd'] and i + 1 < len(path_parts):
                product_id = path_parts[i + 1]
                break
        
        if 'amzn.eu' in parsed.netloc:
            return f"https://www.amazon.fr/dp/{product_id}"
        
        if product_id:
            return f"https://{parsed.netloc}/dp/{product_id}"
        return url

    async def on_ready(self):
        print(f'{self.user} est connecté et prêt!')

    async def on_message(self, message):
        # Ignore les messages du bot lui-même
        if message.author == self.user:
            return

        # Ne traitez que les messages contenant des liens Amazon
        amazon_url = self.extract_amazon_url(message.content)
        if amazon_url:
            try:
                print(f"URL Amazon détectée : {amazon_url}")
                
                unshortened_url = self.unshorten_url(amazon_url)
                print(f"URL déroulée : {unshortened_url}")
                
                clean_url = self.clean_amazon_url(unshortened_url)
                print(f"URL nettoyée : {clean_url}")
                
                if '?tag=' not in clean_url:
                    affiliate_url = f"{clean_url}?tag={self.affiliate_tag}"
                else:
                    affiliate_url = clean_url.split('?tag=')[0] + f"?tag={self.affiliate_tag}"
                print(f"URL avec affiliation : {affiliate_url}")
                
                try:
                    short_url = self.shortener.tinyurl.short(affiliate_url)
                    print(f"URL raccourcie : {short_url}")
                except Exception as e:
                    print(f"Erreur lors du raccourcissement : {e}")
                    short_url = affiliate_url
                
                author_name = message.author.display_name
                
                try:
                    await message.delete()
                    await message.channel.send(
                        f"💫 **{author_name}** a partagé : {short_url}"
                    )
                except discord.Forbidden:
                    await message.channel.send(
                        f"🛒 Voici le lien affilié : {short_url}"
                    )
                    
            except Exception as e:
                print(f"Erreur lors du traitement du lien : {e}")
        else:
            # Si ce n'est pas un lien Amazon, traitez les commandes normalement
            await self.process_commands(message)
