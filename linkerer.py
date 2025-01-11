# Mejoras en las importaciones y organización
from __future__ import annotations  # Para anotaciones de tipo más modernas
import aiohttp
import aiofiles
import asyncio
import json
import logging
import os
import random
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal
from aiohttp import ClientSession
from dataclasses import dataclass
from pathlib import Path
from sourcesv1 import CONSULTAS, RUTA_SALIDA, USER_AGENTS

# Configuración de logging mejorada
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

# Usando dataclasses para mejor estructura
@dataclass
class ScraperConfig:
    calls_per_second: float = 0.2
    min_delay: float = 2.0
    max_delay: float = 4.0
    min_page_delay: float = 4.0
    max_page_delay: float = 6.0
    min_domain_delay: float = 8.0
    max_domain_delay: float = 12.0
    api_timeout: int = 30
    api_endpoint: str = 'http://172.16.1.2:5000/shortener/'

# Constantes en mayúsculas y agrupadas
GOOGLE_ERROR_TERMS = ['unusual traffic', 'captcha']
SUCCESS_STATUS_CODES = {200, 202}
ERROR_429 = "ERROR_429"

# Mejora en el manejo de patrones excluidos
class PatternMatcher:
    def __init__(self, patterns: List[str]):
        self.patterns = [re.compile(pattern) for pattern in patterns]
    
    def matches(self, url: str) -> bool:
        return any(pattern.match(url) for pattern in self.patterns)

pattern_matcher = PatternMatcher([
    r'https://www\.elmostrador\.cl/noticias/pais/$',
     r'https://www\.meganoticias\.cl/nacional/\?page=\d+$',
    r'https://www\.24horas\.cl/actualidad/nacional/p/\d+$',
    r'https://www\.24horas\.cl/actualidad/nacional\?$',
    r'https://www\.24horas\.cl/actualidad/nacional$',
    r'https://cambio21\.cl/politica$',
    r'https://www\.df\.cl/mercados$',
    r'https://www\.eldinamo\.cl/pais/page/\d+/$',
    r'https://www\.elciudadano\.com/actualidad/page/\d+/$',
    r'https://www\.elciudadano\.com/actualidad/\?filter_by=\w+$',
    r'https://www\.elciudadano\.com/actualidad/\?amp$',
    r'https://www\.chilevision\.cl/noticias/nacional/?(\?.*)?$',
    r'https://www\.adnradio\.cl/noticias/$',
    r'https://www\.adnradio\.cl/noticias/economia/$',
    r'https://www\.adnradio\.cl/noticias/nacional/$',
    r'https://www\.adnradio\.cl/noticias/politica/$',
    r'https://www\.eldinamo\.cl/pais/page/\d+/\?page=\d+$',
    r'https://www\.24horas\.cl/deportes$',
    r'https://www\.24horas\.cl/deportes/futbol-internacional$',
    r'https://www\.24horas\.cl/deportes/futbol-nacional$',
    r'https://www\.24horas\.cl/deportes/futbol-nacional/colo-colo$',
    r'https://www\.ex-ante\.cl/$',
    r'https://www\.cnnchile\.com/deportes/$',
    r'https://www\.adnradio\.cl/noticias/ciencia-y-tecnologia/$',
    r'https://www\.publimetro\.cl/deportes/$',
    r'https://puranoticia\.pnt\.cl/nacional/$'
])

class RateLimiter:
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0.0
        self.lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self.lock:
            current_time = datetime.now().timestamp()
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < 1.0 / self.calls_per_second:
                await asyncio.sleep(1.0 / self.calls_per_second - time_since_last_call)
            self.last_call_time = datetime.now().timestamp()

class GoogleScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.calls_per_second)

    def get_headers(self) -> Dict[str, str]:
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
        try:
            await asyncio.sleep(random.uniform(self.config.min_delay, self.config.max_delay))
            async with session.get(url, headers=headers) as response:
                if response.status == 429:
                    logger.warning(f"Google bloqueó el acceso (429) para {url}")
                    return ERROR_429
                if response.status != 200:
                    logger.warning(f"Status code {response.status} para {url}")
                    return None
                return await response.text()
        except Exception as err:
            logger.error(f"Error al solicitar {url}: {err}")
            return None

    def extract_links(self, html: str, source: str, category: str, page: int) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        results = soup.find_all('div', class_='yuRUbf')
        links = [result.find('a')['href'] for result in results if result.find('a')]
        
        if links:
            logger.info(
                f"Encontrados {len(links)} enlaces para {source} - "
                f"Categoría: {category} (página {page + 1})"
            )
        return links

    @staticmethod
    def clean_links(links: List[str]) -> List[str]:
        cleaned = []
        for link in links:
            clean_link = re.sub(r"(?:\?.*?utm.*|&.*|#.*)", "", link)
            if not pattern_matcher.matches(clean_link):
                cleaned.append(clean_link)
        return list(set(cleaned))

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
        
        if links == ERROR_429:
            return ERROR_429
            
        if links:
            all_links.extend(links)
            
            # Solo intentar segunda página si encontramos 10 enlaces en la primera
            if len(links) == 10:
                await asyncio.sleep(random.uniform(
                    self.config.min_page_delay,
                    self.config.max_page_delay
                ))
                links_page2 = await self.fetch_google_links(session, query, page=1)
                
                if links_page2 == ERROR_429:
                    return ERROR_429
                    
                if links_page2:
                    all_links.extend(links_page2)
        
        clean_links = self.clean_links(all_links)
        
        return [{
            **query,
            "url": link,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        } for link in clean_links]

    async def fetch_google_links(
        self,
        session: ClientSession,
        query: Dict[str, str],
        page: int = 0
    ) -> List[str] | Literal["ERROR_429"]:
        """Realiza una búsqueda en Google y obtiene los enlaces."""
        await self.rate_limiter.wait()

        start = page * 10
        url = (
            f"https://www.google.cl/search?q=site:{query['site']}"
            f"+after:{datetime.now().strftime('%Y-%m-%d')}"
            f"+{query['category'].lower()}"
            f"{'&start=' + str(start) if start > 0 else ''}"
        )
        
        html = await self.fetch_page(session, url, self.get_headers())
        
        if html == ERROR_429:
            return ERROR_429
        elif html is None:
            return []
            
        if any(term in html.lower() for term in GOOGLE_ERROR_TERMS):
            logger.warning(f"Google detectó tráfico inusual para {query['source']}")
            return ERROR_429
            
        return self.extract_links(html, query['source'], query['category'], page)

    async def process_sources(
        self,
        session: ClientSession,
        queries: List[Dict]
    ) -> List[Dict]:
        """Procesa todas las fuentes de forma secuencial con rate limiting."""
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
                
                if isinstance(results, str) and results == ERROR_429:
                    logger.warning(
                        f"Se detectó bloqueo de Google (429) para {domain}. "
                        "Guardando resultados obtenidos..."
                    )
                    return all_results
                
                if results:
                    all_results.extend(results)
                
            await asyncio.sleep(random.uniform(
                self.config.min_domain_delay,
                self.config.max_domain_delay
            ))
        
        return all_results

class ResultsManager:
    def __init__(self, output_path: Path):
        self.output_path = Path(output_path)

    async def load_previous_results(self) -> List[Dict]:
        current_hour = datetime.now()
        previous_hour = current_hour - timedelta(hours=1)
        
        # Intentar archivo de hora anterior
        filename = f'linkerer_{previous_hour.strftime("%Y%m%d_%H")}.json'
        result = await self._try_load_file(filename)
        if result:
            return result

        # Si es madrugada, intentar archivo de 23h del día anterior
        if 0 <= current_hour.hour <= 6:
            filename = f'linkerer_{(current_hour - timedelta(days=1)).strftime("%Y%m%d_23")}.json'
            result = await self._try_load_file(filename)
            if result:
                return result

        return []

    async def _try_load_file(self, filename: str) -> Optional[List[Dict]]:
        file_path = self.output_path / filename
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.error(f"Error al cargar {file_path}: {e}")
            return None

    @staticmethod
    def filter_new_results(new_results: List[Dict], previous_results: List[Dict]) -> List[Dict]:
        previous_urls = {r['url'] for r in previous_results}
        return [r for r in new_results if r['url'] not in previous_urls]

    async def save_results(self, results: List[Dict]) -> Optional[Path]:
        if not results:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H")
        file_path = self.output_path / f'linkerer_{timestamp}.json'
        
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(results, indent=2, ensure_ascii=False))
            return file_path
        except Exception as e:
            logger.error(f"Error al guardar resultados: {e}")
            return None

async def send_to_api(
    session: ClientSession,
    file_path: Path,
    config: ScraperConfig
) -> bool:
    """Envía los resultados al API de shortener."""
    if not file_path:
        return False
        
    try:
        data = aiohttp.FormData()
        data.add_field('file', 
                      open(file_path, 'rb'),
                      filename=file_path.name)
        
        async with session.post(
            config.api_endpoint,
            data=data,
            timeout=config.api_timeout
        ) as response:
            if response.status in SUCCESS_STATUS_CODES:
                response_data = await response.json()
                logger.info(
                    f"Archivo {file_path.name} recibido por el shortener. "
                    f"{response_data.get('message', '')}"
                )
                return True
            else:
                logger.error(
                    f"El shortener no pudo recibir el archivo: {response.status}"
                )
                return False
    except Exception as e:
        logger.error(f"Error al intentar enviar al shortener: {str(e)}")
        return False

async def main():
    """Función principal mejorada."""
    config = ScraperConfig()
    scraper = GoogleScraper(config)
    results_manager = ResultsManager(Path(RUTA_SALIDA))

    try:
        # Inicializar el cliente HTTP con timeout y reintentos
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            raise_for_status=True
        ) as session:
            results = await scraper.process_sources(session, CONSULTAS)
            
            if not results:
                logger.info("No se encontraron resultados")
                return

            previous_results = await results_manager.load_previous_results()
            filtered_results = results_manager.filter_new_results(results, previous_results)

            if not filtered_results:
                logger.info("No hay nuevos resultados únicos")
                return

            if output_file := await results_manager.save_results(filtered_results):
                if await send_to_api(session, output_file, config):
                    logger.info(
                        f"Proceso completado. {len(filtered_results)} nuevos "
                        "resultados enviados al shortener"
                    )
                else:
                    logger.error("No se pudo enviar el archivo al shortener")

    except Exception as e:
        logger.exception("Error en la ejecución principal")

if __name__ == "__main__":
    asyncio.run(main())
