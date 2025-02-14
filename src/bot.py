import discord
from discord.ext import commands
import re
import requests
import os
from urllib.parse import urlparse, parse_qs

class AmazonAffiliateBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Récupération du tag d'affiliation depuis les variables d'environnement
        self.affiliate_tag = os.getenv('AFFILIATE_TAG')

    async def setup_hook(self):
        print("Bot is setting up...")

    def extract_amazon_urls(self, content):
        # Liste des patterns pour détecter différents formats d'URLs Amazon
        amazon_regex = r'https?://(?:www\.)?amazon\.(?:com|fr|co\.uk|de|it|es)/[^\s]+(?:[^\s.,!?;:]|[.,!?;:](?=\s|$))'
        urls = []
        
        # Recherche des URLs Amazon standards dans le message
        matches = re.finditer(amazon_regex, content)
        for match in matches:
            url = match.group(0).rstrip('.,!?;:')  # Supprime la ponctuation finale
            # Ignore les URLs qui ne sont pas des produits
            if not any(keyword in url.lower() for keyword in [
                'mission', 
                'hz/mobile',
                'signin',
                'register',
                'ap/'
            ]):
                urls.append(url)
        
        # Gestion des liens courts Amazon
        short_regex = r'https?://(?:amzn\.(?:to|eu)|a\.co)/[^\s]+(?:[^\s.,!?;:]|[.,!?;:](?=\s|$))'
        short_matches = re.finditer(short_regex, content)
        for match in short_matches:
            url = match.group(0).rstrip('.,!?;:')
            urls.append(url)
        
        return urls

    def unshorten_url(self, url):
        try:
            # Configuration de la session avec un User-Agent pour éviter les blocages
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # Suit les redirections pour obtenir l'URL finale
            response = session.get(url, headers=headers, allow_redirects=True, timeout=5)
            return response.url
        except Exception as e:
            print(f"Erreur lors du déroulage de l'URL : {e}")
            return url

    def get_product_id(self, url):
        try:
            # Nettoyage de l'URL
            url = url.rstrip('.,!?;:')
            
            # Liste des mots-clés à ignorer
            ignored_patterns = [
                'mission',
                'hz/mobile',
                'signin',
                'register',
                'ap/',
                'ref=',
                'ref_='
            ]
            
            # Vérifie si l'URL contient un mot-clé à ignorer
            if any(pattern in url.lower() for pattern in ignored_patterns):
                print(f"URL ignorée car ce n'est pas un lien de produit : {url}")
                return None
            
            # Patterns pour extraire l'ID du produit
            patterns = [
                r'/dp/([A-Z0-9]{10})',
                r'/gp/product/([A-Z0-9]{10})',
                r'/product/([A-Z0-9]{10})',
                r'(?<=/)[A-Z0-9]{10}(?=/|$)',
                r'/d/([A-Z0-9]{10})'
            ]
        
            # Teste chaque pattern pour trouver l'ID
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            print(f"Aucun ID de produit trouvé dans l'URL : {url}")
            return None
            
        except Exception as e:
            print(f"Erreur lors de l'extraction de l'ID du produit : {e}")
            return None

    def create_short_amazon_url(self, product_id):
        # Crée l'URL courte avec le tag d'affiliation
        return f"https://www.amazon.fr/dp/{product_id}?tag={self.affiliate_tag}"

    async def on_ready(self):
        print(f'{self.user} est connecté et prêt!')

    async def on_message(self, message):
        # Ignore les messages du bot lui-même
        if message.author == self.user:
            return

        # Extraction des URLs Amazon du message
        amazon_urls = self.extract_amazon_urls(message.content)
        if amazon_urls:
            try:
                affiliate_links = []
                
                # Traitement de chaque URL trouvée
                for amazon_url in amazon_urls:
                    print(f"URL Amazon détectée : {amazon_url}")
                    
                    # Déroulage des liens courts
                    if 'amzn.to' in amazon_url or 'amzn.eu' in amazon_url:
                        amazon_url = self.unshorten_url(amazon_url)
                    
                    # Extraction de l'ID et création du lien d'affiliation
                    product_id = self.get_product_id(amazon_url)
                    if product_id:
                        short_url = self.create_short_amazon_url(product_id)
                        affiliate_links.append(short_url)
                        print(f"URL courte générée : {short_url}")
                
                # Si des liens ont été générés, envoie le message formaté
                if affiliate_links:
                    author_name = message.author.display_name
                    links_message = "\n".join(affiliate_links)
                    
                    # Suppression du message original
                    try:
                        await message.delete()
                        print("Message original supprimé avec succès")
                    except (discord.Forbidden, discord.NotFound, Exception) as e:
                        print(f"Erreur lors de la suppression du message : {e}")
                    
                    # Envoi du nouveau message avec les liens d'affiliation
                    try:
                        await message.channel.send(
                            f"💫 **{author_name}** a partagé :\n{links_message}"
                        )
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du nouveau message : {e}")
                        # Message de fallback si le formatage échoue
                        await message.channel.send(
                            f"🛒 Voici les liens :\n{links_message}"
                        )
                        
            except Exception as e:
                print(f"Erreur lors du traitement des liens : {e}")
        else:
            await self.process_commands(message)
