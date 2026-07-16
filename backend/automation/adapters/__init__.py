from backend.automation.adapters.ashby import AshbyAdapter
from backend.automation.adapters.base import AdapterConfig, BaseATSAdapter
from backend.automation.adapters.detector import (
    ATSPlatform,
    PlatformDetection,
    detect_from_page,
    detect_from_url,
)
from backend.automation.adapters.greenhouse import GreenhouseAdapter
from backend.automation.adapters.lever import LeverAdapter
from backend.automation.adapters.workable import WorkableAdapter

__all__ = [
    "ATSPlatform",
    "AdapterConfig",
    "AshbyAdapter",
    "BaseATSAdapter",
    "GreenhouseAdapter",
    "LeverAdapter",
    "PlatformDetection",
    "WorkableAdapter",
    "detect_from_page",
    "detect_from_url",
]
