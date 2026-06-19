"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'services.orchestration.application.orchestrator' modülüne yönlendirme yapmaktadır.
Yeni geliştirmelerde doğrudan 'application.orchestrator' kullanılmalıdır.
"""

from services.orchestration.application.orchestrator import (
    CentralExecutive,
    central_executive,
    orchestrator
)
