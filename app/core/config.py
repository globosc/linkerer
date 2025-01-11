from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from typing import List, Dict, Set, Optional
from datetime import datetime

class Settings(BaseSettings):
    """
    Configuración de la aplicación usando Pydantic BaseSettings.
    Las variables pueden ser sobreescritas por variables de entorno.
    """
    # Configuración básica de la aplicación
    APP_NAME: str = "Linkerer API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Rutas de archivos
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    OUTPUT_DIR: Path = PROJECT_ROOT / "output"
    LOG_FILE: Path = PROJECT_ROOT / "logs/scraper.log"
    
    # Configuración del scraper
    CALLS_PER_SECOND: float = 0.2
    MIN_DELAY: float = 2.0
    MAX_DELAY: float = 4.0
    MIN_PAGE_DELAY: float = 4.0
    MAX_PAGE_DELAY: float = 6.0
    MIN_DOMAIN_DELAY: float = 8.0
    MAX_DOMAIN_DELAY: float = 12.0
    
    # Configuración HTTP y API
    API_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3
    HTTP_MAX_CONNECTIONS: int = 10
    HTTP_SSL_VERIFY: bool = False
    SHORTENER_API_URL: str = "http://172.16.1.2:5000/shortener/"
    
    # Estados y códigos
    SUCCESS_STATUS_CODES: Set[int] = {200, 202}
    ERROR_429: str = "ERROR_429"
    GOOGLE_ERROR_TERMS: List[str] = ['unusual traffic', 'captcha']
    
    # Headers por defecto
    DEFAULT_HEADERS: Dict[str, str] = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive'
    }
    
    # User Agents
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    ]
    
    # Patrones de exclusión
    EXCLUDED_PATTERNS: List[str] = [
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
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_output_dir(self) -> Path:
        """Asegura que el directorio de salida existe y lo retorna."""
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return self.OUTPUT_DIR

    def get_log_dir(self) -> Path:
        """Asegura que el directorio de logs existe y lo retorna."""
        log_dir = self.LOG_FILE.parent
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    
    def get_file_name(self, timestamp: Optional[datetime] = None) -> str:
        """Genera el nombre del archivo basado en timestamp."""
        if timestamp is None:
            timestamp = datetime.now()
        return f'linkerer_{timestamp.strftime("%Y%m%d_%H")}.json'

@lru_cache()
def get_settings() -> Settings:
    """Retorna una instancia cacheada de la configuración."""
    return Settings()

# Instancia global de configuración
settings = get_settings()