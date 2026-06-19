"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'services.orchestration.application.control' modülüne yönlendirme yapmaktadır.
Yeni geliştirmelerde doğrudan 'application.control' kullanılmalıdır.
"""

from services.orchestration.application.control import (
    SystemControl,
    system_control,
    control
)
