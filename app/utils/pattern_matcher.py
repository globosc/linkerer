import re
from typing import List
import logging
from ..core.config import settings

class PatternMatcher:
    """
    Clase para manejar los patrones de exclusión de URLs.
    Compila los patrones regex una sola vez para mejor rendimiento.
    """
    def __init__(self, patterns: List[str] = None):
        """
        Inicializa el matcher con una lista de patrones regex.
        
        Args:
            patterns (List[str], optional): Lista de patrones regex.
                                          Si no se proporciona, usa los de settings.
        """
        self.logger = logging.getLogger(__name__)
        self.patterns = self._compile_patterns(patterns or settings.EXCLUDED_PATTERNS)
        
    def _compile_patterns(self, patterns: List[str]) -> List[re.Pattern]:
        """
        Compila los patrones regex.
        
        Args:
            patterns (List[str]): Lista de patrones a compilar
            
        Returns:
            List[re.Pattern]: Lista de patrones compilados
        """
        compiled_patterns = []
        for pattern in patterns:
            try:
                compiled_patterns.append(re.compile(pattern))
            except re.error as e:
                self.logger.error(f"Error al compilar patrón '{pattern}': {e}")
        return compiled_patterns
    
    def matches(self, url: str) -> bool:
        """
        Verifica si una URL coincide con alguno de los patrones de exclusión.
        
        Args:
            url (str): URL a verificar
            
        Returns:
            bool: True si la URL coincide con algún patrón, False en caso contrario
        """
        for pattern in self.patterns:
            if pattern.match(url):
                return True
        return False

    def clean_url(self, url: str) -> str:
        """
        Limpia una URL removiendo parámetros UTM y fragmentos.
        
        Args:
            url (str): URL a limpiar
            
        Returns:
            str: URL limpia
        """
        return re.sub(r"(?:\?.*?utm.*|&.*|#.*)", "", url)
    
    def filter_urls(self, urls: List[str], clean: bool = True) -> List[str]:
        """
        Filtra una lista de URLs, excluyendo las que coinciden con los patrones.
        Opcionalmente limpia las URLs antes de filtrar.
        
        Args:
            urls (List[str]): Lista de URLs a filtrar
            clean (bool): Si es True, limpia las URLs antes de filtrar
            
        Returns:
            List[str]: Lista de URLs filtradas
        """
        filtered = []
        for url in urls:
            clean_url = self.clean_url(url) if clean else url
            if not self.matches(clean_url):
                filtered.append(clean_url)
        
        excluded_count = len(urls) - len(filtered)
        if excluded_count > 0:
            self.logger.info(f"Excluidas {excluded_count} URLs según patrones")
            
        return list(set(filtered))  # Elimina duplicados

# Ejemplo de uso:
"""
# Usando patrones por defecto de settings
matcher = PatternMatcher()

# O con patrones personalizados
custom_patterns = [
    r'https://example\.com/exclude/.*',
    r'https://another\.com/skip/.*'
]
custom_matcher = PatternMatcher(custom_patterns)

# Verificar una URL
url = "https://www.elmostrador.cl/noticias/pais/"
if matcher.matches(url):
    print("URL excluida")

# Limpiar y filtrar varias URLs
urls = [
    "https://example.com/article?utm_source=facebook",
    "https://valid.com/news",
    "https://excluded.com/skip"
]
filtered_urls = matcher.filter_urls(urls)
"""