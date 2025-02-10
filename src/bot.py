import discord
from discord.ext import commands
import re
import requests
import os
from urllib.parse import urlparse, parse_qs

class AmazonAffiliateBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.affiliate_tag = os.getenv('AFFILIATE_TAG')

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

    def get_product_id(self, url):
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/d/([A-Z0-9]{10})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def create_short_amazon_url(self, product_id):
        return f"https://amzn.eu/d/{product_id}"

    async def on_ready(self):
        print(f'{self.user} est connecté et prêt!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        amazon_url = self.extract_amazon_url(message.content)
        if amazon_url:
            try:
                print(f"URL Amazon détectée : {amazon_url}")
                
                unshortened_url = self.unshorten_url(amazon_url)
                print(f"URL déroulée : {unshortened_url}")
                
                product_id = self.get_product_id(unshortened_url)
                if product_id:
                    short_url = self.create_short_amazon_url(product_id)
                    print(f"URL courte générée : {short_url}")
                    
                    if '?tag=' not in short_url:
                        affiliate_url = f"{short_url}?tag={self.affiliate_tag}"
                    else:
                        affiliate_url = short_url.split('?tag=')[0] + f"?tag={self.affiliate_tag}"
                    print(f"URL avec affiliation : {affiliate_url}")
                    
                    author_name = message.author.display_name
                    
                    try:
                        await message.delete()
                        await message.channel.send(
                            f"💫 **{author_name}** a partagé : {affiliate_url}"
                        )
                    except discord.Forbidden:
                        await message.channel.send(
                            f"🛒 Voici le lien affilié : {affiliate_url}"
                        )
                else:
                    print("Impossible d'extraire l'ID du produit")
                    
            except Exception as e:
                print(f"Erreur lors du traitement du lien : {e}")
        else:
            await self.process_commands(message)
