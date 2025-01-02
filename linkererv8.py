import aiohttp
import asyncio
import json
import logging
import os
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
from aiohttp import ClientSession
from sourcesv1 import CONSULTAS, RUTA_SALIDA, USER_AGENTS
import re

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Patrones excluidos precompilados para mejor rendimiento
PATRONES_EXCLUIDOS = [re.compile(patron) for patron in [
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
]]

class RateLimiter:
    def __init__(self, calls_per_second=1):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            current_time = datetime.now().timestamp()
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < 1.0 / self.calls_per_second:
                await asyncio.sleep(1.0 / self.calls_per_second - time_since_last_call)
            self.last_call_time = datetime.now().timestamp()

def obtener_user_agent():
    """Devuelve un User-Agent aleatorio de la lista."""
    return random.choice(USER_AGENTS)

async def obtener_enlaces_google(consulta: Dict, session: ClientSession, pagina: int = 0, rate_limiter: RateLimiter = None) -> List[str]:
    """Realiza una búsqueda en Google y obtiene los enlaces de resultados."""
    if rate_limiter:
        await rate_limiter.wait()

    start = pagina * 10
    url = (
        f"https://www.google.cl/search?q=site:{consulta['site']}"
        f"+after:{datetime.now().strftime('%Y-%m-%d')}"
        f"+{consulta['category'].lower()}"
        f"{'&start=' + str(start) if start > 0 else ''}"
    )
    
    headers = {
        'User-Agent': obtener_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    }

    try:
        await asyncio.sleep(random.uniform(2, 4))
        
        async with session.get(url, headers=headers) as response:
            if response.status == 429:
                logger.warning(f"Google bloqueó el acceso (429) para {consulta['source']}")
                return "ERROR_429"
                
            if response.status != 200:
                logger.warning(f"Status code {response.status} para {consulta['source']}")
                return []
                
            text = await response.text()
            if any(term in text.lower() for term in ['unusual traffic', 'captcha']):
                logger.warning(f"Google detectó tráfico inusual para {consulta['source']}")
                return "ERROR_429"
                
            soup = BeautifulSoup(text, 'html.parser')
            resultados = soup.find_all('div', class_='yuRUbf')
            enlaces = [resultado.find('a')['href'] for resultado in resultados if resultado.find('a')]
            
            if enlaces:
                logger.info(f"Encontrados {len(enlaces)} enlaces para {consulta['source']} - Categoría: {consulta['category']} (página {pagina + 1})")
            
            await asyncio.sleep(random.uniform(3, 5))
            return enlaces
            
    except Exception as err:
        logger.error(f"Error al solicitar {consulta['source']}: {err}")
        return []

def limpiar_enlaces(enlaces: List[str]) -> List[str]:
    """Limpia y filtra los enlaces."""
    enlaces_filtrados = []
    for enlace in enlaces:
        enlace_limpio = re.sub(r"(?:\?.*?utm.*|&.*|#.*)", "", enlace)
        if not any(patron.match(enlace_limpio) for patron in PATRONES_EXCLUIDOS):
            enlaces_filtrados.append(enlace_limpio)
    return list(set(enlaces_filtrados))

async def procesar_fuente(consulta: Dict, session: ClientSession, rate_limiter: RateLimiter) -> List[Dict]:
    """Procesa una fuente incluyendo múltiples páginas solo si es necesario."""
    logger.info(f"Procesando fuente: {consulta['source']} - Categoría: {consulta['category']}")
    todos_enlaces = []
    
    # Obtener primera página
    enlaces = await obtener_enlaces_google(consulta, session, 0, rate_limiter)
    
    if enlaces == "ERROR_429":
        return "ERROR_429"
        
    if enlaces:
        todos_enlaces.extend(enlaces)
        
        # Solo intentar segunda página si encontramos 10 enlaces en la primera
        if len(enlaces) == 10:
            await asyncio.sleep(random.uniform(4, 6))
            enlaces_pagina2 = await obtener_enlaces_google(consulta, session, 1, rate_limiter)
            
            if enlaces_pagina2 == "ERROR_429":
                return "ERROR_429"
                
            if enlaces_pagina2:
                todos_enlaces.extend(enlaces_pagina2)
    
    enlaces_limpios = limpiar_enlaces(todos_enlaces)
    
    return [{
        **consulta,
        "url": enlace,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    } for enlace in enlaces_limpios]

async def cargar_resultados_hora_anterior() -> List[Dict]:
    """Carga los resultados de la hora anterior o de las 23h del día anterior si es madrugada."""
    hora_actual = datetime.now()
    
    # Intentar cargar archivo de la hora anterior
    hora_anterior = (hora_actual - timedelta(hours=1)).strftime("%Y%m%d_%H")
    ruta_archivo = os.path.join(RUTA_SALIDA, f'linkerer_{hora_anterior}.json')
    
    # Si no existe y estamos en la madrugada (0-6 am), buscar archivo de las 23h del día anterior
    if not os.path.exists(ruta_archivo) and 0 <= hora_actual.hour <= 6:
        ultimo_archivo = (hora_actual - timedelta(days=1)).strftime("%Y%m%d_23")
        ruta_archivo = os.path.join(RUTA_SALIDA, f'linkerer_{ultimo_archivo}.json')
    
    if os.path.exists(ruta_archivo):
        try:
            with open(ruta_archivo, 'r') as f:
                resultados = json.load(f)
                logger.info(f"Comparando con archivo: {os.path.basename(ruta_archivo)}")
                return resultados
        except Exception as e:
            logger.error(f"Error al cargar {ruta_archivo}: {e}")
    else:
        logger.info("No se encontró archivo anterior para comparar duplicados")
    
    return []

def filtrar_nuevos_resultados(nuevos: List[Dict], anteriores: List[Dict]) -> List[Dict]:
    """Filtra los resultados nuevos eliminando duplicados."""
    urls_anteriores = {r['url'] for r in anteriores}
    return [r for r in nuevos if r['url'] not in urls_anteriores]

def guardar_resultados(resultados: List[Dict]) -> str:
    """Guarda los resultados en un archivo JSON."""
    if not resultados:
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H")
    ruta_archivo = os.path.join(RUTA_SALIDA, f'linkerer_{timestamp}.json')
    
    try:
        os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        return ruta_archivo
    except Exception as e:
        logger.error(f"Error al guardar resultados: {e}")
        return None

async def enviar_a_api(ruta_archivo: str) -> bool:
    """Envía los resultados al API de shortener y termina cuando confirma la recepción."""
    if not ruta_archivo:
        return False
        
    try:
        async with ClientSession() as session:
            with open(ruta_archivo, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=os.path.basename(ruta_archivo))
                
                # Solo esperamos la respuesta inicial del shortener
                async with session.post(
                    'http://172.16.1.2:5000/shortener/',
                    data=data,
                    timeout=30
                ) as response:
                    # Aceptamos tanto 200 como 202 (Accepted)
                    if response.status in [200, 202]:
                        response_data = await response.json()
                        logger.info(f"Archivo {os.path.basename(ruta_archivo)} recibido por el shortener. {response_data.get('message', '')}")
                        return True
                    else:
                        logger.error(f"El shortener no pudo recibir el archivo: {response.status}")
                        return False
    except Exception as e:
        logger.error(f"Error al intentar enviar al shortener: {str(e)}")
        return False

async def procesar_fuentes_secuencial(consultas: List[Dict]) -> List[Dict]:
    """Procesa las fuentes de forma secuencial con rate limiting."""
    todos_resultados = []
    rate_limiter = RateLimiter(calls_per_second=0.2)
    
    # Agrupar consultas por dominio base
    dominios = {}
    for consulta in consultas:
        dominio_base = re.search(r'https?://[^/]+', consulta['site']).group()
        if dominio_base not in dominios:
            dominios[dominio_base] = []
        dominios[dominio_base].append(consulta)
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with ClientSession(connector=connector) as session:
        for dominio, consultas_dominio in dominios.items():
            for consulta in consultas_dominio:
                resultados = await procesar_fuente(consulta, session, rate_limiter)
                
                if isinstance(resultados, str) and resultados == "ERROR_429":
                    logger.warning(f"Se detectó bloqueo de Google (429) para {dominio}. Guardando resultados obtenidos...")
                    return todos_resultados
                
                if resultados:
                    todos_resultados.extend(resultados)
                
            await asyncio.sleep(random.uniform(8, 12))
    
    return todos_resultados

async def main():
    """Función principal."""
    try:
        todos_resultados = await procesar_fuentes_secuencial(CONSULTAS)
        
        if not todos_resultados:
            logger.info("No se encontraron resultados")
            return
            
        resultados_anteriores = await cargar_resultados_hora_anterior()
        resultados_filtrados = filtrar_nuevos_resultados(todos_resultados, resultados_anteriores)
        
        if not resultados_filtrados:
            logger.info("No hay nuevos resultados únicos")
            return
            
        # Guardar y enviar resultados una sola vez
        if ruta_archivo := guardar_resultados(resultados_filtrados):
            if await enviar_a_api(ruta_archivo):
                logger.info(f"Proceso completado. {len(resultados_filtrados)} nuevos resultados enviados al shortener")
            else:
                logger.error("No se pudo enviar el archivo al shortener")
                
    except Exception as e:
        logger.exception("Error en la ejecución principal")

if __name__ == "__main__":
    asyncio.run(main())