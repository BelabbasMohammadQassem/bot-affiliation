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

    def extract_amazon_urls(self, content):
        # Liste des patterns pour détecter différents formats d'URLs Amazon
        patterns = [
            r'https?://(?:www\.)?amazon\.(?:com|fr|co\.uk|de|it|es)/[^\s]+',
            r'https?://amzn\.(?:to|eu)/[^\s]+',
            r'https?://a\.co/d/[^\s]+'
        ]

        urls = []
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Nettoyer l'URL en retirant la ponctuation finale
                url = match.group(0).rstrip('.,!?;:')
                # Nettoyer les paramètres superflus
                base_url = url.split('?')[0]
                urls.append(base_url)
        
        return urls

    def unshorten_url(self, url):
        try:
            # Nettoyer l'URL avant de la dérouler
            url = url.rstrip('.,!?;:')
            
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = session.get(url, headers=headers, allow_redirects=True, timeout=5)
            
            # Extraire l'URL de base et le product ID
            final_url = response.url
            product_id = self.get_product_id(final_url)
            
            if product_id:
                # Créer une URL propre avec juste l'ID du produit
                return f"https://www.amazon.fr/dp/{product_id}"
            return final_url
            
        except Exception as e:
            print(f"Erreur lors du déroulage de l'URL : {e}")
            return url

    def get_product_id(self, url):
        try:
            # Nettoyer l'URL et supprimer les paramètres
            url = url.rstrip('.,!?;:')
            url = url.split('?')[0]
            
            # Liste des mots-clés à ignorer
            ignored_patterns = [
                'mission',
                'hz/mobile',
                'signin',
                'register',
                'ap/',
                'ref=',
                'ref_=',
                'deals',
                'gp/browse',
                'gp/goldbox'
            ]
            
            if any(pattern in url.lower() for pattern in ignored_patterns):
                print(f"URL ignorée car ce n'est pas un lien de produit : {url}")
                return None
            
            patterns = [
                r'/dp/([A-Z0-9]{10})',
                r'/gp/product/([A-Z0-9]{10})',
                r'/product/([A-Z0-9]{10})',
                r'(?<=/)[A-Z0-9]{10}(?=/|$)',
                r'/d/([A-Z0-9]{10})'
            ]
        
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"Erreur lors de l'extraction de l'ID du produit : {e}")
            return None

    def create_short_amazon_url(self, product_id):
        return f"https://www.amazon.fr/dp/{product_id}?tag={self.affiliate_tag}"

    async def on_ready(self):
        print(f'{self.user} est connecté et prêt!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        amazon_urls = self.extract_amazon_urls(message.content)
        if amazon_urls:
            try:
                affiliate_links = []
                
                for amazon_url in amazon_urls:
                    print(f"URL Amazon détectée : {amazon_url}")
                    
                    # Si c'est un lien court, le dérouler d'abord
                    if any(domain in amazon_url for domain in ['amzn.to', 'amzn.eu', 'a.co']):
                        amazon_url = self.unshorten_url(amazon_url)
                    
                    product_id = self.get_product_id(amazon_url)
                    if product_id:
                        short_url = self.create_short_amazon_url(product_id)
                        affiliate_links.append(short_url)
                        print(f"URL courte générée : {short_url}")
                
                if affiliate_links:
                    author_name = message.author.display_name
                    links_message = "\n".join(affiliate_links)
                    
                    try:
                        await message.delete()
                        print("Message original supprimé avec succès")
                    except (discord.Forbidden, discord.NotFound, Exception) as e:
                        print(f"Erreur lors de la suppression du message : {e}")
                    
                    try:
                        await message.channel.send(
                            f"💫 **{author_name}** a partagé :\n{links_message}"
                        )
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du nouveau message : {e}")
                        await message.channel.send(
                            f"🛒 Voici les liens :\n{links_message}"
                        )
                        
            except Exception as e:
                print(f"Erreur lors du traitement des liens : {e}")
        else:
            await self.process_commands(message)
