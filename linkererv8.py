import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import random
import logging
import os
import asyncio
import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector, FormData
from typing import List, Dict, Optional
from sourcesv1 import RUTA_SALIDA, USER_AGENTS, CONSULTAS
from contextlib import asynccontextmanager

# Configuración de logging con rotación de archivos
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class NewsScraperConfig:
    TIMEOUT = ClientTimeout(total=30)
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    CONCURRENT_REQUESTS = 5
    
    # Precompilación de patrones
    PATRONES_EXCLUIDOS = [re.compile(patron) for patron in [
        r'https://www.elmostrador.cl/noticias/pais/$',
        r'https://www.meganoticias.cl/nacional/\?page=\d+$',
        r'https://www.24horas.cl/actualidad/nacional/p/\d+$',
        r'https://www.24horas.cl/actualidad/nacional\?$',
        r'https://www.24horas.cl/actualidad/nacional$',
        r'https://cambio21.cl/politica$',
        r'https://www.df.cl/mercados$',
        r'https://www.eldinamo.cl/pais/page/\d+/$',
        r'https://www.elciudadano.com/actualidad/page/\d+/$',
        r'https://www.elciudadano.com/actualidad/\?filter_by=\w+$',
        r'https://www.elciudadano.com/actualidad/\?amp$',
        r'https://www.chilevision.cl/noticias/nacional/?(\?.*)?$',
        r'https://www.adnradio.cl/noticias/$',
        r'https://www.adnradio.cl/noticias/economia/$',
        r'https://www.adnradio.cl/noticias/nacional/$',
        r'https://www.adnradio.cl/noticias/politica/$',
        r'https://www.eldinamo.cl/pais/page/\d+/\?page=\d+$',
        r'https://www.24horas.cl/deportes$',
        r'https://www.24horas.cl/deportes/futbol-internacional$',
        r'https://www.24horas.cl/deportes/futbol-nacional$',
        r'https://www.24horas.cl/deportes/futbol-nacional/colo-colo$',
        r'https://www.ex-ante.cl/$',
        r'https://www.cnnchile.com/deportes/$',
        r'https://www.adnradio.cl/noticias/ciencia-y-tecnologia/$',
        r'https://www.publimetro.cl/deportes/$',
        r'https://puranoticia.pnt.cl/nacional/$'
    ]]

class NewsScraper:
    def __init__(self):
        self.config = NewsScraperConfig()
        self.semaphore = asyncio.Semaphore(self.config.CONCURRENT_REQUESTS)

    @staticmethod
    def obtener_user_agent():
        """Devuelve un User-Agent aleatorio de la lista."""
        return random.choice(USER_AGENTS)

    @asynccontextmanager
    async def get_session(self):
        """Gestiona la sesión HTTP de manera segura."""
        connector = TCPConnector(ssl=False, limit=self.config.CONCURRENT_REQUESTS)
        async with ClientSession(
            connector=connector,
            timeout=self.config.TIMEOUT,
            headers={'User-Agent': self.obtener_user_agent()}
        ) as session:
            yield session

    async def obtener_enlaces_google(self, consulta: Dict, session: ClientSession) -> List[str]:
        """Realiza una búsqueda en Google con mejor manejo de límites de frecuencia."""
        url = f"https://www.google.cl/search?q=site:{consulta['site']}+after:{datetime.now().strftime('%Y-%m-%d')}"
        
        async with self.semaphore:
            for intento in range(self.config.MAX_RETRIES):
                try:
                    # Delay aleatorio más largo entre intentos
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    # Rotar User-Agent en cada intento
                    headers = {
                        'User-Agent': self.obtener_user_agent(),
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
    
                    async with session.get(url, headers=headers, timeout=30) as response:
                        text = await response.text()
                        
                        # Verificar si Google está bloqueando las peticiones
                        if "unusual traffic" in text.lower() or "captcha" in text.lower():
                            logging.warning(f"Google detectó tráfico inusual para {consulta['source']}. Esperando antes de reintentar...")
                            await asyncio.sleep(10 + random.uniform(1, 5))
                            continue
                            
                        if response.status == 200:
                            soup = BeautifulSoup(text, 'html.parser')
                            resultados = soup.find_all('div', class_='yuRUbf')
                            
                            if not resultados:
                                logging.warning(f"No se encontraron resultados para {consulta['source']} (posible bloqueo)")
                                continue
                                
                            enlaces = [resultado.find('a')['href'] for resultado in resultados if resultado.find('a')]
                            if enlaces:
                                logging.info(f"Encontrados {len(enlaces)} enlaces para {consulta['source']}")
                                return enlaces
                                
                        elif response.status == 429:  # Too Many Requests
                            logging.warning(f"Rate limit alcanzado para {consulta['source']}. Esperando...")
                            await asyncio.sleep(15 + random.uniform(1, 5))
                            continue
                        else:
                            response.raise_for_status()
                            
                except asyncio.TimeoutError:
                    logging.error(f"Timeout al buscar {consulta['source']}")
                    await asyncio.sleep(5)
                except Exception as err:
                    logging.error(f"Error al buscar {consulta['source']}: {str(err)}")
                    await asyncio.sleep(5)
                    
            logging.error(f"No se pudieron obtener resultados para {consulta['source']} después de {self.config.MAX_RETRIES} intentos")
            return []

    def limpiar_y_filtrar_enlaces(self, enlaces: List[str]) -> List[str]:
        """Limpia y filtra enlaces usando sets para mejor rendimiento."""
        enlaces_unicos = set()
        for enlace in enlaces:
            enlace_limpio = re.sub(r"(?:\?.*?utm.*|&.*|#.*)", "", enlace)
            if not any(patron.match(enlace_limpio) for patron in self.config.PATRONES_EXCLUIDOS):
                enlaces_unicos.add(enlace_limpio)
            else:
                logging.info(f"Enlace excluido por patrón: {enlace_limpio}")
        return list(enlaces_unicos)

    async def generar_resultados(self) -> List[Dict]:
        """Genera los resultados manteniendo todos los campos de la fuente."""
        async with self.get_session() as session:
            tareas = [self.obtener_enlaces_google(consulta, session) for consulta in CONSULTAS]
            resultados = await asyncio.gather(*tareas)

        resultados_finales = []
        for consulta, enlaces in zip(CONSULTAS, resultados):
            enlaces_filtrados = self.limpiar_y_filtrar_enlaces(enlaces)
            for enlace in enlaces_filtrados:
                # Creamos una copia del diccionario de consulta original
                resultado = consulta.copy()
                # Actualizamos los campos necesarios
                resultado.update({
                    "url": enlace,
                    "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                resultados_finales.append(resultado)
        return resultados_finales

    async def cargar_resultados_anteriores(self) -> List[Dict]:
        """Carga resultados anteriores de forma más eficiente."""
        hora_actual = datetime.now()
        resultados_anteriores = []

        for i in range(1, 25):
            hora_anterior = (hora_actual - timedelta(hours=i)).strftime("%Y%m%d_%H")
            ruta = os.path.join(RUTA_SALIDA, f'linkerer_{hora_anterior}.json')
            if os.path.exists(ruta):
                try:
                    with open(ruta, 'r') as archivo:
                        resultados_anteriores.extend(json.load(archivo))
                except Exception as e:
                    logging.error(f"Error leyendo archivo {ruta}: {e}")

        return resultados_anteriores

    def guardar_resultados(self, resultados: List[Dict]) -> Optional[str]:
        """Guarda los resultados con manejo de errores mejorado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H")
        nombre_archivo = os.path.join(RUTA_SALIDA, f'linkerer_{timestamp}.json')
        
        try:
            os.makedirs(os.path.dirname(nombre_archivo), exist_ok=True)
            with open(nombre_archivo, 'w', encoding='utf-8') as archivo:
                json.dump(resultados, archivo, indent=2, ensure_ascii=False)
            logging.info(f"Archivo guardado: {nombre_archivo}")
            return nombre_archivo
        except Exception as e:
            logging.error(f"Error guardando resultados: {e}")
            return None

    async def enviar_a_api(self, nombre_archivo: str) -> bool:
        """Envía resultados a la API de forma asincrónica."""
        api_url = "http://192.168.2.113:5000/shortener/"

        try:
            async with self.get_session() as session:
                # Abrir el archivo en modo binario
                with open(nombre_archivo, 'rb') as file:
                    # Crear el FormData correctamente
                    data = FormData()
                    data.add_field(
                        'file',
                        file,
                        filename=os.path.basename(nombre_archivo),
                        content_type='application/json'
                    )

                    # Establecer el header específico para multipart/form-data
                    headers = {
                        'Content-Type': 'multipart/form-data'
                    }

                    # Realizar la petición POST
                    async with session.post(api_url, data=data, headers=headers, timeout=30) as response:
                        if response.status == 200:
                            result = await response.json()
                            logging.info(f"API response: {result}")
                            return True
                        else:
                            error_text = await response.text()
                            logging.error(f"Error en la API (status {response.status}): {error_text}")
                            return False

        except asyncio.TimeoutError:
            logging.error(f"Timeout al enviar a API después de 30 segundos")
            return False
        except Exception as e:
            logging.error(f"Error enviando a API: {str(e)}")
            return False

    def filtrar_nuevos_resultados(self, resultados_nuevos: List[Dict], 
                                resultados_anteriores: List[Dict]) -> List[Dict]:
        """Filtra los resultados nuevos eliminando duplicados."""
        urls_anteriores = {resultado['url'] for resultado in resultados_anteriores}
        return [resultado for resultado in resultados_nuevos 
                if resultado['url'] not in urls_anteriores]

async def main():
    """Función principal con mejor manejo de errores."""
    try:
        scraper = NewsScraper()
        
        # Cargar resultados anteriores
        resultados_anteriores = await scraper.cargar_resultados_anteriores()
        
        # Generar nuevos resultados
        resultados_nuevos = await scraper.generar_resultados()

        if not resultados_nuevos:
            logging.info("No se encontraron nuevos resultados")
            return

        # Filtrar resultados duplicados
        resultados_filtrados = scraper.filtrar_nuevos_resultados(
            resultados_nuevos, 
            resultados_anteriores
        )

        if not resultados_filtrados:
            logging.info("No hay nuevos resultados después de filtrar")
            return

        # Guardar y enviar resultados
        if nombre_archivo := scraper.guardar_resultados(resultados_filtrados):
            await scraper.enviar_a_api(nombre_archivo)
        else:
            logging.error("No se pudo guardar el archivo de resultados")

    except Exception as e:
        logging.exception(f"Error en main: {e}")

if __name__ == "__main__":
    asyncio.run(main())