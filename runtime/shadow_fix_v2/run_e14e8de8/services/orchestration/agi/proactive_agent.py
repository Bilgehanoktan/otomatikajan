"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'services.orchestration.application.proactive_agent' modülüne yönlendirme yapmaktadır.
Yeni projelerde doğrudan 'application.proactive_agent' kullanılmalıdır.
"""

from services.orchestration.application.proactive_agent import (
    ProactiveAgent,
    proactive_agent
)
