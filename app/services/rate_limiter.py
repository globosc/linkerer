from datetime import datetime
import asyncio
import random
from typing import Optional
from ..core.config import settings

class RateLimiter:
    """
    Controla la tasa de peticiones con diferentes niveles de delay.
    Incluye delays específicos para peticiones generales, entre páginas y entre dominios.
    """
    def __init__(self, calls_per_second: float = settings.CALLS_PER_SECOND):
        self.calls_per_second = calls_per_second
        self.last_call_time = 0.0
        self.lock = asyncio.Lock()

    async def wait(self) -> None:
        """
        Espera el tiempo necesario para mantener la tasa de llamadas dentro del límite.
        También aplica un delay aleatorio entre min_delay y max_delay.
        """
        async with self.lock:
            current_time = datetime.now().timestamp()
            time_since_last_call = current_time - self.last_call_time
            
            if time_since_last_call < 1.0 / self.calls_per_second:
                await asyncio.sleep(1.0 / self.calls_per_second - time_since_last_call)
            
            # Aplicar delay base
            await asyncio.sleep(
                random.uniform(settings.MIN_DELAY, settings.MAX_DELAY)
            )
            
            self.last_call_time = datetime.now().timestamp()

    async def page_delay(self) -> None:
        """
        Aplica un delay específico entre peticiones de páginas del mismo dominio.
        Este delay es más largo que el delay base.
        """
        await asyncio.sleep(
            random.uniform(settings.MIN_PAGE_DELAY, settings.MAX_PAGE_DELAY)
        )

    async def domain_delay(self) -> None:
        """
        Aplica un delay entre peticiones a diferentes dominios.
        Este es el delay más largo para evitar detección.
        """
        await asyncio.sleep(
            random.uniform(settings.MIN_DOMAIN_DELAY, settings.MAX_DOMAIN_DELAY)
        )

    async def with_rate_limit(self, func, *args, **kwargs):
        """
        Decorator asíncrono para aplicar rate limiting a cualquier función.
        
        Args:
            func: Función a ejecutar con rate limiting
            *args: Argumentos posicionales para la función
            **kwargs: Argumentos nombrados para la función
            
        Returns:
            El resultado de la función ejecutada
        """
        await self.wait()
        return await func(*args, **kwargs)

# Ejemplo de uso:
"""
limiter = RateLimiter()

# Uso básico
await limiter.wait()

# Entre páginas del mismo dominio
await limiter.page_delay()

# Entre diferentes dominios
await limiter.domain_delay()

# Como wrapper de función
async def make_request():
    # ... código de la petición ...
    pass

result = await limiter.with_rate_limit(make_request)
"""