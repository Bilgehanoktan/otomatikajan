class LLMError(Exception):
    """LLM operasyonları için temel hata sınıfı."""
    pass

class RateLimitError(LLMError):
    """Sağlayıcı limitleri aşıldığında (429) fırlatılır."""
    pass

class EmptyResponseError(LLMError):
    """LLM boş metin döndüğünde fırlatılır."""
    pass

class ExhaustedFallbackError(LLMError):
    """Tüm yedek modeller denendiği halde başarılı olunamadığında fırlatılır."""
    pass