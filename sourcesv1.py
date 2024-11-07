import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

# Configuración de la carpeta de salida
RUTA_SALIDA = "/home/globoscx/unews/salidas/input"
os.makedirs(RUTA_SALIDA, exist_ok=True)

# Definir los User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/88.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
]

# Mantener la lista original de CONSULTAS
CONSULTAS = [
    {
        "category": "Nacional",
        "site": "https://www.latercera.com/nacional/noticia/",
        "source": "La Tercera",
        "diminutive": "LT",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "COPESA",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.biobiochile.cl/noticias/nacional/",
        "source": "Radio BioBio",
        "diminutive": "RBB",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Bío-Bío Comunicaciones",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.emol.com/noticias/Nacional/",
        "source": "EMOL",
        "diminutive": "EMOL",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "El Mercurio S.A.P.",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.eldesconcierto.cl/nacional/",
        "source": "El Desconcierto",
        "diminutive": "ELDS",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.eldinamo.cl/pais/",
        "source": "El Dinamo",
        "diminutive": "ELDI",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente*",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.elciudadano.com/actualidad/",
        "source": "El Ciudadano",
        "diminutive": "ELCI",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://cambio21.cl/politica",
        "source": "Cambio21",
        "diminutive": "C21",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.df.cl/mercados/",
        "source": "Diario Financiero",
        "diminutive": "DF",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Grupo Claro",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.chilevision.cl/noticias/nacional/",
        "source": "Chilevision",
        "diminutive": "CHV",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Paramount Global",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.24horas.cl/actualidad/nacional/",
        "source": "24 Horas",
        "diminutive": "24H",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "TVN",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.cooperativa.cl/noticias/pais/",
        "source": "Cooperativa",
        "diminutive": "Coop",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.cnnchile.com/pais/",
        "source": "CNN Chile",
        "diminutive": "CNN",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "CNN",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.t13.cl/noticia/nacional/",
        "source": "Teletrece",
        "diminutive": "T13",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "TV Medios",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.elmostrador.cl/noticias/pais/",
        "source": "El Mostrador",
        "diminutive": "ELMO",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.publimetro.cl/noticias/",
        "source": "Publimetro",
        "diminutive": "PM",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.meganoticias.cl/nacional/",
        "source": "Meganoticias",
        "diminutive": "MEGA",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Megamedia",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.adnradio.cl/noticias/",
        "source": "ADN",
        "diminutive": "ADN",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Ibero Americana Radio Chile",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Nacional",
        "site": "https://www.ex-ante.cl/",
        "source": "EX-ANTE",
        "diminutive": "EX",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.latercera.com/el-deportivo/noticia/",
        "source": "La Tercera Deportes",
        "diminutive": "LT",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Copesa",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.biobiochile.cl/noticias/deportes/",
        "source": "Radio BioBio",
        "diminutive": "RBB",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Bío-Bío Comunicaciones",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.emol.com/noticias/Deportes/",
        "source": "EMOL",
        "diminutive": "EMOL",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "El Mercurio S.A.P.",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.eldinamo.cl/deportes/",
        "source": "El Dinamo",
        "diminutive": "ELDI",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente*",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.chilevision.cl/chv-deportes/noticias/",
        "source": "Chilevision",
        "diminutive": "CHV",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Paramount Global",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.24horas.cl/deportes/",
        "source": "24 Horas",
        "diminutive": "24H",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "TVN",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.alairelibre.cl/noticias/deportes/",
        "source": "Al Aire Libre",
        "diminutive": "ADN",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Compañía Chilena de Comunicaciones",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.cnnchile.com/deportes/",
        "source": "CNN Chile",
        "diminutive": "CNN",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "CNN",
        "update_frequency": "hourly",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.deportes13.cl/futbol-chileno/",
        "source": "Teletrece",
        "diminutive": "T13",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.publimetro.cl/deportes/",
        "source": "Publimetro",
        "diminutive": "PM",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://www.meganoticias.cl/deportes/",
        "source": "Meganoticias",
        "diminutive": "MEGA",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Megamedia",
        "update_frequency": "daily",
        "content_type": "article"
    },
    {
        "category": "Deportes",
        "site": "https://ellibero.cl/actualidad/",
        "source": "El Libero",
        "diminutive": "LIBERO",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },    
    {
        "category": "Nacional",
        "site": "https://puranoticia.pnt.cl/nacional/",
        "source": "Puranoticia",
        "diminutive": "Puranoticia",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },      
    {
        "category": "Nacional",
        "site": "https://www.diariousach.cl/actualidad/nacional",
        "source": "Diario USACH",
        "diminutive": "USACH",
        "content_length": "",
        "sentiment": "",
        "keywords": "",
        "popularity": "",
        "subcategory": "",
        "holding": "Independiente",
        "update_frequency": "daily",
        "content_type": "article"
    },
]

# Agregar las mejoras manteniendo la compatibilidad
class NewsSourceManager:
    def __init__(self, consultas: List[Dict]):
        self.consultas = consultas
        self.path = Path(RUTA_SALIDA)

    def get_sources_by_category(self, category: str) -> List[Dict]:
        """Obtiene fuentes filtradas por categoría."""
        return [source for source in self.consultas 
                if source["category"].lower() == category.lower()]

    def get_hourly_sources(self) -> List[Dict]:
        """Obtiene las fuentes que necesitan actualización horaria."""
        return [source for source in self.consultas 
                if source["update_frequency"] == "hourly"]

    def get_independent_sources(self) -> List[Dict]:
        """Obtiene las fuentes independientes."""
        return [source for source in self.consultas 
                if "independiente" in source["holding"].lower()]

    def get_sources_by_holding(self, holding: str) -> List[Dict]:
        """Obtiene fuentes filtradas por holding."""
        return [source for source in self.consultas 
                if source["holding"].lower() == holding.lower()]

    def get_source_stats(self) -> Dict:
        """Obtiene estadísticas de las fuentes."""
        categories = set(source["category"] for source in self.consultas)
        holdings = set(source["holding"] for source in self.consultas)
        
        return {
            "total_sources": len(self.consultas),
            "categories": {
                category: len(self.get_sources_by_category(category))
                for category in categories
            },
            "update_frequency": {
                "hourly": len(self.get_hourly_sources()),
                "daily": len([s for s in self.consultas if s["update_frequency"] == "daily"])
            },
            "holdings": {
                holding: len(self.get_sources_by_holding(holding))
                for holding in holdings
            },
            "independent_sources": len(self.get_independent_sources())
        }

    def export_stats(self, filename: str = "sources_stats.json") -> None:
        """Exporta las estadísticas a un archivo JSON."""
        stats = self.get_source_stats()
        output_path = self.path.parent / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

    def validate_sources(self) -> List[Dict]:
        """Valida las fuentes y retorna errores encontrados."""
        errors = []
        required_fields = ["category", "site", "source", "diminutive", "holding"]
        
        for source in self.consultas:
            source_errors = {
                "source": source["source"],
                "errors": []
            }
            
            # Validar campos requeridos
            for field in required_fields:
                if not source.get(field):
                    source_errors["errors"].append(f"Campo {field} vacío")
            
            # Validar URL
            if not source["site"].startswith("https://"):
                source_errors["errors"].append("URL debe comenzar con https://")
            
            # Validar update_frequency
            if source.get("update_frequency") not in ["hourly", "daily"]:
                source_errors["errors"].append("update_frequency debe ser 'hourly' o 'daily'")
            
            if source_errors["errors"]:
                errors.append(source_errors)
        
        return errors

# Crear una instancia global del manager
source_manager = NewsSourceManager(CONSULTAS)

# Funciones de utilidad para mantener compatibilidad con el código existente
def get_sources_by_category(category: str) -> List[Dict]:
    return source_manager.get_sources_by_category(category)

def get_hourly_sources() -> List[Dict]:
    return source_manager.get_hourly_sources()

def validate_all_sources() -> List[Dict]:
    return source_manager.validate_sources()

def export_source_stats(filename: str = "sources_stats.json") -> None:
    source_manager.export_stats(filename)