"""
Data Acquisition Module.

Handles web scraping with a dual-layer approach to ensure reliable text extraction
while bypassing standard anti-bot protections.
"""

import logging
import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Prepends https:// if the URL scheme is missing."""
    parsed = urlparse(url)
    if not parsed.scheme:
        return f"https://{url}"
    return url


def fetch_with_trafilatura(url: str) -> str | None:
    """Primary extraction: Grabs clean body text, ignoring navbars and footers."""
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        return trafilatura.extract(downloaded, include_links=False, include_images=False)
    return None


def fetch_with_bs4(url: str) -> str | None:
    """Fallback extraction: Triggers if Trafilatura fails or gets blocked."""
    try:
        # Spoof a standard Chrome browser to bypass basic 403 bot protections
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # 10-second timeout prevents the background task queue from hanging
        response = requests.get(url, headers=headers, timeout=10) 
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Target specific tags where business value propositions usually live
        tags = soup.find_all(['h1', 'h2', 'h3', 'p', 'li'])
        text = ' '.join([tag.get_text(strip=True) for tag in tags])
        
        return text if text else None
        
    except Exception as e:
        logger.error(f"BS4 fallback failed for {url}: {e}")
        return None


def scrape_company_data(base_url: str) -> str:
    """
    Scrapes the homepage and /about page to build the LLM's context window.
    """
    base_url = normalize_url(base_url)
    
    # Target root and /about to maximize business context with minimal network requests
    urls_to_scrape = [base_url, urljoin(base_url, '/about')]
    extracted_text = []

    for url in urls_to_scrape:
        logger.info(f"Attempting to scrape: {url}")
        text = fetch_with_trafilatura(url)
        
        if not text:
            logger.info(f"Trafilatura failed for {url}. Engaging BS4 fallback.")
            text = fetch_with_bs4(url)
            
        if text:
            extracted_text.append(f"--- Data from {url} ---\n{text}")

    if not extracted_text:
        # Throwing an error here triggers the orchestrator's 'except' block,
        # ensuring the failure is properly logged to SQLite and Sheets.
        raise ValueError(f"Failed to extract meaningful text from {base_url}")

    return "\n\n".join(extracted_text)