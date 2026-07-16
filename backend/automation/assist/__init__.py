"""AI-Assisted Application Engine.

Components:
- ApplicationAssistant: AI-generated answers for common questions
- ReviewSession: human review + edit + approve before submission
- SessionRecord: full audit trail with step tracking
- ApplicationEngine: end-to-end automated application pipeline
"""

from backend.automation.assist.answers import ApplicationAssistant
from backend.automation.assist.engine import ApplicationEngine
from backend.automation.assist.recorder import SessionRecord, SessionStep
from backend.automation.assist.review import ReviewSession, ReviewStatus

__all__ = [
    "ApplicationAssistant",
    "ApplicationEngine",
    "ReviewSession",
    "ReviewStatus",
    "SessionRecord",
    "SessionStep",
]
