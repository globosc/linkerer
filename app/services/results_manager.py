import aiofiles
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from ..core.config import settings

class ResultsManager:
    """
    Maneja el almacenamiento y recuperación de resultados del scraper,
    incluyendo la lógica para cargar resultados previos y filtrar duplicados.
    """
    def __init__(self, output_path: Optional[Path] = None):
        """
        Inicializa el gestor de resultados.
        
        Args:
            output_path (Path, optional): Ruta del directorio de salida.
                                        Si no se proporciona, usa la del settings.
        """
        self.output_path = Path(output_path or settings.OUTPUT_DIR)
        self.logger = logging.getLogger(__name__)
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Asegura que el directorio de salida existe."""
        self.output_path.mkdir(parents=True, exist_ok=True)

    def _get_filename(self, timestamp: datetime) -> str:
        """
        Genera el nombre del archivo basado en timestamp.
        
        Args:
            timestamp (datetime): Marca de tiempo para el nombre del archivo
            
        Returns:
            str: Nombre del archivo en formato linkerer_YYYYMMDD_HH.json
        """
        return f'linkerer_{timestamp.strftime("%Y%m%d_%H")}.json'

    async def load_previous_results(self) -> List[Dict]:
        """
        Carga los resultados de la hora anterior o del día anterior si es madrugada.
        
        Returns:
            List[Dict]: Lista de resultados previos. Lista vacía si no hay.
        """
        current_hour = datetime.now()
        previous_hour = current_hour - timedelta(hours=1)
        
        # Intentar archivo de hora anterior
        filename = self._get_filename(previous_hour)
        result = await self._try_load_file(filename)
        if result:
            self.logger.info(f"Cargados {len(result)} resultados de la hora anterior")
            return result

        # Si es madrugada (0-6h), intentar archivo de 23h del día anterior
        if 0 <= current_hour.hour <= 6:
            yesterday_23 = current_hour.replace(hour=23) - timedelta(days=1)
            filename = self._get_filename(yesterday_23)
            result = await self._try_load_file(filename)
            if result:
                self.logger.info(f"Cargados {len(result)} resultados del día anterior")
                return result

        self.logger.info("No se encontraron resultados previos")
        return []

    async def _try_load_file(self, filename: str) -> Optional[List[Dict]]:
        """
        Intenta cargar un archivo de resultados.
        
        Args:
            filename (str): Nombre del archivo a cargar
            
        Returns:
            Optional[List[Dict]]: Resultados cargados o None si hay error
        """
        file_path = self.output_path / filename
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            self.logger.error(f"Error al cargar {file_path}: {e}")
            return None

    @staticmethod
    def filter_new_results(
        new_results: List[Dict],
        previous_results: List[Dict]
    ) -> List[Dict]:
        """
        Filtra los resultados nuevos que no están en los resultados previos.
        
        Args:
            new_results (List[Dict]): Nuevos resultados a filtrar
            previous_results (List[Dict]): Resultados previos para comparar
            
        Returns:
            List[Dict]: Lista de resultados únicos
        """
        previous_urls = {r['url'] for r in previous_results}
        filtered_results = [r for r in new_results if r['url'] not in previous_urls]
        
        duplicate_count = len(new_results) - len(filtered_results)
        if duplicate_count > 0:
            logging.info(f"Filtrados {duplicate_count} resultados duplicados")
            
        return filtered_results

    async def save_results(self, results: List[Dict]) -> Optional[Path]:
        """
        Guarda los resultados en un archivo JSON.
        
        Args:
            results (List[Dict]): Resultados a guardar
            
        Returns:
            Optional[Path]: Ruta del archivo guardado o None si hay error
        """
        if not results:
            self.logger.info("No hay resultados para guardar")
            return None
            
        timestamp = datetime.now()
        file_path = self.output_path / self._get_filename(timestamp)
        
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(
                    results,
                    indent=2,
                    ensure_ascii=False
                ))
            self.logger.info(f"Guardados {len(results)} resultados en {file_path}")
            return file_path
        except Exception as e:
            self.logger.error(f"Error al guardar resultados: {e}")
            return None

# Ejemplo de uso:
"""
# Inicializar el gestor
results_manager = ResultsManager()

# Cargar resultados previos
previous_results = await results_manager.load_previous_results()

# Filtrar nuevos resultados
filtered_results = results_manager.filter_new_results(new_results, previous_results)

# Guardar resultados filtrados
output_file = await results_manager.save_results(filtered_results)
"""