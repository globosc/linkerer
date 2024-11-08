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

# Definir categorías como Enum
class NewsCategory(str, Enum):
    NACIONAL = "nacional"
    DEPORTES = "deportes"
    ECONOMIA = "economia"  # Preparado para futura implementación

# Estructura base de un medio
@dataclass
class MediaOutlet:
    name: str
    diminutive: str
    holding: str
    update_frequency: str
    base_url: str
    category_paths: Dict[NewsCategory, str]

# Definir los medios y sus rutas por categoría
MEDIA_OUTLETS = {
    "latercera": MediaOutlet(
        name="La Tercera",
        diminutive="LT",
        holding="COPESA",
        update_frequency="hourly",
        base_url="https://www.latercera.com",
        category_paths={
            NewsCategory.NACIONAL: "/nacional/noticia/",
            NewsCategory.DEPORTES: "/el-deportivo/noticia/",
        }
    ),
    "biobio": MediaOutlet(
        name="Radio BioBio",
        diminutive="RBB",
        holding="Bío-Bío Comunicaciones",
        update_frequency="hourly",
        base_url="https://www.biobiochile.cl",
        category_paths={
            NewsCategory.NACIONAL: "/noticias/nacional/",
            NewsCategory.DEPORTES: "/noticias/deportes/",
        }
    ),
    "emol": MediaOutlet(
        name="EMOL",
        diminutive="EMOL",
        holding="El Mercurio S.A.P.",
        update_frequency="hourly",
        base_url="https://www.emol.com",
        category_paths={
            NewsCategory.NACIONAL: "/noticias/Nacional/",
            NewsCategory.DEPORTES: "/noticias/Deportes/",
        }
    ),
    "eldesconcierto": MediaOutlet(
        name="El Desconcierto",
        diminutive="ELDS",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://www.eldesconcierto.cl",
        category_paths={
            NewsCategory.NACIONAL: "/nacional/",
        }
    ),
    "eldinamo": MediaOutlet(
        name="El Dinamo",
        diminutive="ELDI",
        holding="Independiente*",
        update_frequency="daily",
        base_url="https://www.eldinamo.cl",
        category_paths={
            NewsCategory.NACIONAL: "/pais/",
            NewsCategory.DEPORTES: "/deportes/",
        }
    ),
    "elciudadano": MediaOutlet(
        name="El Ciudadano",
        diminutive="ELCI",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://www.elciudadano.com",
        category_paths={
            NewsCategory.NACIONAL: "/actualidad/",
        }
    ),
    "cambio21": MediaOutlet(
        name="Cambio21",
        diminutive="C21",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://cambio21.cl",
        category_paths={
            NewsCategory.NACIONAL: "/politica",
        }
    ),
    "df": MediaOutlet(
        name="Diario Financiero",
        diminutive="DF",
        holding="Grupo Claro",
        update_frequency="daily",
        base_url="https://www.df.cl",
        category_paths={
            NewsCategory.NACIONAL: "/mercados/",
        }
    ),
    "chilevision": MediaOutlet(
        name="Chilevision",
        diminutive="CHV",
        holding="Paramount Global",
        update_frequency="hourly",
        base_url="https://www.chilevision.cl",
        category_paths={
            NewsCategory.NACIONAL: "/noticias/nacional/",
            NewsCategory.DEPORTES: "/chv-deportes/noticias/",
        }
    ),
    "24horas": MediaOutlet(
        name="24 Horas",
        diminutive="24H",
        holding="TVN",
        update_frequency="hourly",
        base_url="https://www.24horas.cl",
        category_paths={
            NewsCategory.NACIONAL: "/actualidad/nacional/",
            NewsCategory.DEPORTES: "/deportes/",
        }
    ),
    "cooperativa": MediaOutlet(
        name="Cooperativa",
        diminutive="Coop",
        holding="Independiente",
        update_frequency="hourly",
        base_url="https://www.cooperativa.cl",
        category_paths={
            NewsCategory.NACIONAL: "/noticias/pais/",
        }
    ),
    "cnnchile": MediaOutlet(
        name="CNN Chile",
        diminutive="CNN",
        holding="CNN",
        update_frequency="hourly",
        base_url="https://www.cnnchile.com",
        category_paths={
            NewsCategory.NACIONAL: "/pais/",
            NewsCategory.DEPORTES: "/deportes/",
        }
    ),
    "t13": MediaOutlet(
        name="Teletrece",
        diminutive="T13",
        holding="TV Medios",
        update_frequency="hourly",
        base_url="https://www.t13.cl",
        category_paths={
            NewsCategory.NACIONAL: "/noticia/nacional/",
        }
    ),
    "elmostrador": MediaOutlet(
        name="El Mostrador",
        diminutive="ELMO",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://www.elmostrador.cl",
        category_paths={
            NewsCategory.NACIONAL: "/noticias/pais/",
        }
    ),
    "publimetro": MediaOutlet(
        name="Publimetro",
        diminutive="PM",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://www.publimetro.cl",
        category_paths={
            NewsCategory.NACIONAL: "/noticias/",
            NewsCategory.DEPORTES: "/deportes/",
        }
    ),
    "meganoticias": MediaOutlet(
        name="Meganoticias",
        diminutive="MEGA",
        holding="Megamedia",
        update_frequency="daily",
        base_url="https://www.meganoticias.cl",
        category_paths={
            NewsCategory.NACIONAL: "/nacional/",
            NewsCategory.DEPORTES: "/deportes/",
        }
    ),
    "adn": MediaOutlet(
        name="ADN",
        diminutive="ADN",
        holding="Ibero Americana Radio Chile",
        update_frequency="hourly",
        base_url="https://www.adnradio.cl",
        category_paths={
            NewsCategory.NACIONAL: "/noticias/",
        }
    ),
    "exante": MediaOutlet(
        name="EX-ANTE",
        diminutive="EX",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://www.ex-ante.cl",
        category_paths={
            NewsCategory.NACIONAL: "/",
        }
    ),
    "alaire": MediaOutlet(
        name="Al Aire Libre",
        diminutive="AAL",
        holding="Compañía Chilena de Comunicaciones",
        update_frequency="daily",
        base_url="https://www.alairelibre.cl",
        category_paths={
            NewsCategory.DEPORTES: "/noticias/deportes/",
        }
    ),
    "ellibero": MediaOutlet(
        name="El Libero",
        diminutive="LIBERO",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://ellibero.cl",
        category_paths={
            NewsCategory.NACIONAL: "/actualidad/",
        }
    ),
    "puranoticia": MediaOutlet(
        name="Puranoticia",
        diminutive="Puranoticia",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://puranoticia.pnt.cl",
        category_paths={
            NewsCategory.NACIONAL: "/nacional/",
        }
    ),
    "diariousach": MediaOutlet(
        name="Diario USACH",
        diminutive="USACH",
        holding="Independiente",
        update_frequency="daily",
        base_url="https://www.diariousach.cl",
        category_paths={
            NewsCategory.NACIONAL: "/actualidad/nacional",
        }
    ),
}

def generate_consultas(categories: List[NewsCategory] = None) -> List[Dict]:
    """
    Genera la lista de consultas basada en los medios y categorías especificadas.
    """
    if categories is None:
        categories = list(NewsCategory)

    consultas = []
    for outlet in MEDIA_OUTLETS.values():
        for category in categories:
            if category in outlet.category_paths:
                consultas.append({
                    "category": category.value.capitalize(),
                    "site": outlet.base_url + outlet.category_paths[category],
                    "source": f"{outlet.name}{' ' + category.value.capitalize() if category != NewsCategory.NACIONAL else ''}",
                    "diminutive": outlet.diminutive,
                    "content_length": "",
                    "sentiment": "",
                    "keywords": "",
                    "popularity": "",
                    "subcategory": "",
                    "holding": outlet.holding,
                    "update_frequency": outlet.update_frequency,
                    "content_type": "article"
                })
    
    return consultas

class NewsSourceManager:
    def __init__(self, media_outlets: Dict[str, MediaOutlet]):
        self.media_outlets = media_outlets
        self.consultas = generate_consultas()
        self.path = Path(RUTA_SALIDA)

    def get_sources_by_category(self, category: NewsCategory) -> List[Dict]:
        """Obtiene fuentes filtradas por categoría."""
        return [source for source in self.consultas 
                if source["category"].lower() == category.value.lower()]

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
        """Obtiene estadísticas detalladas de las fuentes."""
        categories = set(source["category"] for source in self.consultas)
        holdings = set(source["holding"] for source in self.consultas)
        
        return {
            "total_sources": len(self.consultas),
            "categories": {
                category: len(self.get_sources_by_category(NewsCategory(category.lower())))
                for category in categories
            },
            "update_frequency": {
                "hourly": len(self.get_hourly_sources()),
                "daily": len([s for s in self.consultas if s["update_frequency"] == "daily"])
            },
            "holdings": {
                holding: len(self.get_sources_by_holding(holding))
                for holding in holdings if holding
            },
            "independent_sources": len(self.get_independent_sources())
        }

    def validate_sources(self) -> List[Dict]:
        """Valida las fuentes y retorna errores encontrados."""
        errors = []
        required_fields = ["category", "site", "source", "diminutive", "holding"]
        
        for source in self.consultas:
            source_errors = {
                "source": source["source"],
                "errors": []
            }
            
            for field in required_fields:
                if not source.get(field):
                    source_errors["errors"].append(f"Campo {field} vacío")
            
            if not source["site"].startswith("https://"):
                source_errors["errors"].append("URL debe comenzar con https://")
            
            if source.get("update_frequency") not in ["hourly", "daily"]:
                source_errors["errors"].append("update_frequency debe ser 'hourly' o 'daily'")
            
            if source_errors["errors"]:
                errors.append(source_errors)
        
        return errors

    def export_stats(self, filename: str = "sources_stats.json") -> None:
        """Exporta las estadísticas a un archivo JSON."""
        stats = self.get_source_stats()
        output_path = self.path.parent / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

# Generar las consultas finales
CONSULTAS = generate_consultas()

# Crear una instancia global del manager
source_manager = NewsSourceManager(MEDIA_OUTLETS)