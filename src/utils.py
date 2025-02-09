import re
import os
from typing import Optional
import pyshorteners

def shorten_url(url):
    s = pyshorteners.Shortener()
    try:
        return s.tinyurl.short(url)
    except:
        return url  # Retourne l'URL originale en cas d'erreur
        
def is_amazon_link(url: str, amazon_domains: list) -> bool:
    """Vérifie si l'URL est un lien Amazon valide."""
    return any(domain in url.lower() for domain in amazon_domains)

def add_affiliate_tag(url: str, tag: str) -> str:
    """Ajoute le tag d'affiliation à l'URL Amazon."""
    # Supprime les paramètres existants
    base_url = url.split('?')[0]
    
    # Ajoute le tag d'affiliation
    return f"{base_url}?tag={tag}"

def extract_amazon_url(text: str, amazon_domains: list) -> Optional[str]:
    """Extrait l'URL Amazon d'un texte."""
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
    
    for url in urls:
        if is_amazon_link(url, amazon_domains):
            return url
    return None
