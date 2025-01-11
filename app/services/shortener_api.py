import aiohttp
from pathlib import Path
from typing import Optional, Dict
import logging
from ..core.config import settings

class ShortenerAPIService:
    """
    Servicio para interactuar con el API del shortener.
    Maneja el envío de archivos y la comunicación con el servicio.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_url = settings.SHORTENER_API_URL
        self.timeout = settings.API_TIMEOUT

    async def send_file(
        self,
        session: aiohttp.ClientSession,
        file_path: Path,
        retries: int = 3
    ) -> bool:
        """
        Envía un archivo al API del shortener.
        
        Args:
            session (aiohttp.ClientSession): Sesión HTTP para hacer la petición
            file_path (Path): Ruta al archivo a enviar
            retries (int): Número de intentos en caso de fallo
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        if not file_path or not file_path.exists():
            self.logger.error("Archivo no encontrado o ruta inválida")
            return False

        attempt = 0
        while attempt < retries:
            try:
                result = await self._try_send_file(session, file_path)
                if result:
                    return True
                    
                attempt += 1
                if attempt < retries:
                    self.logger.warning(
                        f"Reintentando envío ({attempt + 1}/{retries})"
                    )
            except Exception as e:
                self.logger.error(f"Error en intento {attempt + 1}: {str(e)}")
                attempt += 1

        return False

    async def _try_send_file(
        self,
        session: aiohttp.ClientSession,
        file_path: Path
    ) -> bool:
        """
        Intenta enviar un archivo al API.
        
        Args:
            session (aiohttp.ClientSession): Sesión HTTP
            file_path (Path): Ruta al archivo
            
        Returns:
            bool: True si el envío fue exitoso
            
        Raises:
            Exception: Si hay algún error en el proceso
        """
        try:
            data = aiohttp.FormData()
            data.add_field(
                'file',
                open(file_path, 'rb'),
                filename=file_path.name
            )

            async with session.post(
                self.api_url,
                data=data,
                timeout=self.timeout
            ) as response:
                if response.status in settings.SUCCESS_STATUS_CODES:
                    response_data = await response.json()
                    self.logger.info(
                        f"Archivo {file_path.name} recibido por el shortener. "
                        f"{response_data.get('message', '')}"
                    )
                    return True
                else:
                    self.logger.error(
                        f"Error del shortener: {response.status}"
                    )
                    return False

        except aiohttp.ClientError as e:
            self.logger.error(f"Error de conexión: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado: {str(e)}")
            raise

    async def health_check(self, session: aiohttp.ClientSession) -> bool:
        """
        Verifica si el servicio del shortener está disponible.
        
        Args:
            session (aiohttp.ClientSession): Sesión HTTP
            
        Returns:
            bool: True si el servicio responde correctamente
        """
        try:
            health_url = f"{self.api_url.rstrip('/')}/health"
            async with session.get(health_url, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            self.logger.error(f"Error en health check: {str(e)}")
            return False

# Ejemplo de uso:
"""
async def main():
    shortener = ShortenerAPIService()
    
    async with aiohttp.ClientSession() as session:
        # Verificar si el servicio está disponible
        if not await shortener.health_check(session):
            print("Servicio no disponible")
            return
            
        # Enviar archivo
        file_path = Path("output/results_20240111_10.json")
        success = await shortener.send_file(session, file_path)
        
        if success:
            print("Archivo enviado correctamente")
        else:
            print("Error al enviar el archivo")
"""