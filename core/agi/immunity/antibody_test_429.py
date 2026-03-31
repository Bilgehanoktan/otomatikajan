**Antikor (Antibody) implementationu**

Aşağıdaki kod, "RateLimitError" hatasına karşı dayanıklı bir sarma (wrapper) veya dekoratör (decorator) antikor implementasyonunu gösterir:

```python
import functools
import logging
import time

# Logger ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def antibody_retry_on_rate_limit(func):
    """
    Hedef fonksiyonu sarmalayan ve "RateLimitError" hatasına karşı dayanıklı bir antikor.
    
    Args:
        func: Hedef fonksiyon.
    
    Returns:
        Sarılan hedef fonksiyon.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """
        Hedef fonksiyonu çağıran ve "RateLimitError" hatasına karşı dayanıklı bir sarma (wrapper).
        
        Args:
            *args: Hedef fonksiyon argümanları.
            **kwargs: Hedef fonksiyon keyword argümanları.
        
        Returns:
            Hedef fonksiyonun sonucu.
        """
        max_retries = 3  # Maksimum deneme sayısı
        retry_delay = 1  # Yeniden deneme arasında bekleyecek süre (saniye)
        
        for attempt in range(max_retries):
            try:
                # Hedef fonksiyonu çağır
                result = await func(*args, **kwargs)
                return result
            except RateLimitError as e:
                # "RateLimitError" hatası oluştuğunda
                logger.warning(f"RateLimitError: {e}. Deneme {attempt + 1}/{max_retries}")
                # immuno_soft_fallback
                if attempt < max_retries - 1:
                    logger.info(f"Yeniden deneme için {retry_delay} saniye bekleyecek...")
                    time.sleep(retry_delay)
                else:
                    # Tüm denemeler başarısız olduğunda
                    logger.error(f"Tüm denemeler başarısız oldu. Hata: {e}")
                    #Fallback işlemi
                    logger.info("immuno_soft_fallback")
                    return None
    
    return wrapper
```

**Örnek Kullanım:**

```python
@antibody_retry_on_rate_limit
async def example_function():
    # Örnek fonksiyon
    # RateLimitError oluşabilir
    pass
```

Bu antikor, hedef fonksiyonu sarmalayarak "RateLimitError" hatasına karşı dayanıklı bir çözüm sağlar. Hata oluştuğunda, belirtilen maximum deneme sayısına kadar yeniden dener ve her deneme arasında bekler. Tüm denemeler başarısız olduğunda, "immuno_soft_fallback" işlemini gerçekleştirir ve hatayı loglar.
