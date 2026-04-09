"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'packages.orchestration.application.orchestrator' modülüne yönlendirme yapmaktadır.
Yeni geliştirmelerde doğrudan 'application.orchestrator' kullanılmalıdır.
"""

from packages.orchestration.application.orchestrator import (
    CentralExecutive,
    central_executive,
    orchestrator
)
