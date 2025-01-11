# app/services/scraper.py
from typing import List, Dict, Optional, Literal
import logging
import re
from datetime import datetime
import random
from bs4 import BeautifulSoup
import aiohttp
from aiohttp import ClientSession

from ..core.config import GOOGLE_ERROR_TERMS, USER_AGENTS
from ..services.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class GoogleScraper:
    def __init__(self, calls_per_second: float = 0.2):
        self.rate_limiter = RateLimiter(calls_per_second)

    def get_headers(self) -> Dict[str, str]:
        """Genera headers aleatorios para las peticiones."""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }

    async def fetch_page(
        self, 
        session: ClientSession, 
        url: str, 
        headers: Dict[str, str]
    ) -> Optional[str]:
        """Realiza la petición HTTP y maneja errores."""
        try:
            await self.rate_limiter.wait()
            async with session.get(url, headers=headers) as response:
                if response.status == 429:
                    logger.warning(f"Google bloqueó el acceso (429) para {url}")
                    return "ERROR_429"
                if response.status != 200:
                    logger.warning(f"Status code {response.status} para {url}")
                    return None
                return await response.text()
        except Exception as err:
            logger.error(f"Error al solicitar {url}: {err}")
            return None

    def extract_links(self, html: str, source: str, category: str, page: int) -> List[str]:
        """Extrae los enlaces de la página de resultados."""
        soup = BeautifulSoup(html, 'html.parser')
        results = soup.find_all('div', class_='yuRUbf')
        links = [result.find('a')['href'] for result in results if result.find('a')]
        
        if links:
            logger.info(
                f"Encontrados {len(links)} enlaces para {source} - "
                f"Categoría: {category} (página {page + 1})"
            )
        return links

    async def fetch_google_links(
        self,
        session: ClientSession,
        query: Dict[str, str],
        page: int = 0
    ) -> List[str] | Literal["ERROR_429"]:
        """Obtiene enlaces de una página de resultados de Google."""
        start = page * 10
        url = (
            f"https://www.google.cl/search?q=site:{query['site']}"
            f"+after:{datetime.now().strftime('%Y-%m-%d')}"
            f"+{query['category'].lower()}"
            f"{'&start=' + str(start) if start > 0 else ''}"
        )
        
        html = await self.fetch_page(session, url, self.get_headers())
        
        if html == "ERROR_429":
            return "ERROR_429"
        elif html is None:
            return []
            
        if any(term in html.lower() for term in GOOGLE_ERROR_TERMS):
            logger.warning(f"Google detectó tráfico inusual para {query['source']}")
            return "ERROR_429"
            
        return self.extract_links(html, query['source'], query['category'], page)

    async def process_source(
        self,
        session: ClientSession,
        query: Dict[str, str]
    ) -> List[Dict] | Literal["ERROR_429"]:
        """Procesa una fuente individual."""
        logger.info(f"Procesando fuente: {query['source']} - Categoría: {query['category']}")
        all_links = []
        
        # Obtener primera página
        links = await self.fetch_google_links(session, query)
        
        if links == "ERROR_429":
            return "ERROR_429"
            
        if links:
            all_links.extend(links)
            
            # Solo intentar segunda página si encontramos 10 enlaces en la primera
            if len(links) == 10:
                await asyncio.sleep(random.uniform(4, 6))
                links_page2 = await self.fetch_google_links(session, query, page=1)
                
                if links_page2 == "ERROR_429":
                    return "ERROR_429"
                    
                if links_page2:
                    all_links.extend(links_page2)
        
        return [{
            **query,
            "url": link,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        } for link in all_links]

    async def process_sources(
        self,
        session: ClientSession,
        queries: List[Dict]
    ) -> List[Dict]:
        """Procesa todas las fuentes de forma secuencial."""
        all_results = []
        
        # Agrupar consultas por dominio base
        domains = {}
        for query in queries:
            base_domain = re.search(r'https?://[^/]+', query['site']).group()
            if base_domain not in domains:
                domains[base_domain] = []
            domains[base_domain].append(query)
        
        for domain, domain_queries in domains.items():
            for query in domain_queries:
                results = await self.process_source(session, query)
                
                if isinstance(results, str) and results == "ERROR_429":
                    logger.warning(
                        f"Se detectó bloqueo de Google (429) para {domain}. "
                        "Guardando resultados obtenidos..."
                    )
                    return all_results
                
                if results:
                    all_results.extend(results)
                
            await asyncio.sleep(random.uniform(8, 12))
        
        return all_results