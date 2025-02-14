import discord
from discord.ext import commands
import re
import requests
import os
from urllib.parse import urlparse, parse_qs

class AmazonAffiliateBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Récupère le tag d'affiliation depuis les variables d'environnement
        self.affiliate_tag = os.getenv('AFFILIATE_TAG')

    async def setup_hook(self):
        # Méthode appelée lors de l'initialisation du bot
        print("Bot is setting up...")

    def extract_amazon_urls(self, content):
        """
        Extrait toutes les URLs Amazon d'un message
        
        Args:
            content (str): Contenu du message à analyser
            
        Returns:
            list: Liste des URLs Amazon nettoyées
        """
        # Définition des patterns pour différents formats d'URLs Amazon
        patterns = [
            r'https?://(?:www\.)?amazon\.(?:com|fr|co\.uk|de|it|es)/[^\s]+',  # URLs Amazon standards
            r'https?://amzn\.(?:to|eu)/[^\s]+',  # URLs courtes amzn.to/eu
            r'https?://a\.co/d/[^\s]+'  # URLs courtes a.co
        ]

        urls = []
        for pattern in patterns:
            # Recherche toutes les occurrences du pattern dans le message
            matches = re.finditer(pattern, content)
            for match in matches:
                # Nettoie l'URL en retirant la ponctuation et les paramètres
                url = match.group(0).rstrip('.,!?;:')
                base_url = url.split('?')[0]
                urls.append(base_url)
        
        return urls

    def unshorten_url(self, url):
        """
        Déroule une URL courte Amazon pour obtenir l'URL complète
        
        Args:
            url (str): URL courte à dérouler
            
        Returns:
            str: URL complète ou URL d'origine en cas d'erreur
        """
        try:
            url = url.rstrip('.,!?;:')
            
            # Configure une session avec un User-Agent pour éviter les blocages
            session = requests.Session()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # Suit les redirections pour obtenir l'URL finale
            response = session.get(url, headers=headers, allow_redirects=True, timeout=5)
            
            final_url = response.url
            product_id = self.get_product_id(final_url)
            
            # Si un ID de produit est trouvé, crée une URL propre
            if product_id:
                return f"https://www.amazon.fr/dp/{product_id}"
            return final_url
            
        except Exception as e:
            print(f"Erreur lors du déroulage de l'URL : {e}")
            return url

    def get_product_id(self, url):
        """
        Extrait l'ID du produit d'une URL Amazon
        
        Args:
            url (str): URL Amazon à analyser
            
        Returns:
            str: ID du produit ou None si non trouvé/URL invalide
        """
        try:
            # Nettoie l'URL
            url = url.rstrip('.,!?;:')
            url = url.split('?')[0]
            
            # Liste des patterns à ignorer (pages non-produits)
            ignored_patterns = [
                'mission', 'hz/mobile', 'signin', 'register',
                'ap/', 'ref=', 'ref_=', 'deals', 'gp/browse',
                'gp/goldbox'
            ]
            
            # Vérifie si l'URL contient un pattern à ignorer
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
            
            return None
            
        except Exception as e:
            print(f"Erreur lors de l'extraction de l'ID du produit : {e}")
            return None

    def create_short_amazon_url(self, product_id):
        """
        Crée une URL courte Amazon avec le tag d'affiliation
        
        Args:
            product_id (str): ID du produit Amazon
            
        Returns:
            str: URL formatée avec le tag d'affiliation
        """
        return f"https://www.amazon.fr/dp/{product_id}?tag={self.affiliate_tag}"

    async def on_ready(self):
        """Appelé quand le bot est prêt et connecté"""
        print(f'{self.user} est connecté et prêt!')

    async def on_message(self, message):
        """
        Gestionnaire d'événements pour les messages
        Traite les URLs Amazon et les remplace par des liens d'affiliation
        
        Args:
            message: Message Discord reçu
        """
        # Ignore les messages du bot
        if message.author == self.user:
            return

        # Recherche les URLs Amazon dans le message
        amazon_urls = self.extract_amazon_urls(message.content)
        if amazon_urls:
            try:
                affiliate_links = []
                
                # Traite chaque URL trouvée
                for amazon_url in amazon_urls:
                    print(f"URL Amazon détectée : {amazon_url}")
                    
                    # Déroule les liens courts
                    if any(domain in amazon_url for domain in ['amzn.to', 'amzn.eu', 'a.co']):
                        amazon_url = self.unshorten_url(amazon_url)
                    
                    # Génère le lien d'affiliation
                    product_id = self.get_product_id(amazon_url)
                    if product_id:
                        short_url = self.create_short_amazon_url(product_id)
                        affiliate_links.append(short_url)
                        print(f"URL courte générée : {short_url}")
                
                # Si des liens ont été générés, envoie le message formaté
                if affiliate_links:
                    author_name = message.author.display_name
                    links_message = "\n".join(affiliate_links)
                    
                    # Supprime le message original
                    try:
                        await message.delete()
                        print("Message original supprimé avec succès")
                    except (discord.Forbidden, discord.NotFound, Exception) as e:
                        print(f"Erreur lors de la suppression du message : {e}")
                    
                    # Envoie le nouveau message avec les liens d'affiliation
                    try:
                        await message.channel.send(
                            f"💫 **{author_name}** a partagé :\n{links_message}"
                        )
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du nouveau message : {e}")
                        # Message de fallback en cas d'erreur
                        await message.channel.send(
                            f"🛒 Voici les liens :\n{links_message}"
                        )
                        
            except Exception as e:
                print(f"Erreur lors du traitement des liens : {e}")
        else:
            # Si pas d'URLs Amazon, traite les autres commandes
            await self.process_commands(message)
