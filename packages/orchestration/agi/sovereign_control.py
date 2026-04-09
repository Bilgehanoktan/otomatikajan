"""
Faz 12.1 Korumalı Shim Sistemi.
Bu dosya artık 'packages.orchestration.application.control' modülüne yönlendirme yapmaktadır.
Yeni geliştirmelerde doğrudan 'application.control' kullanılmalıdır.
"""

from packages.orchestration.application.control import (
    SystemControl,
    system_control,
    control
)
