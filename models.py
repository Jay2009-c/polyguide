# models.py
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Literal
from enum import Enum


class AnswerStatus(str, Enum):
    GROUNDED = "grounded"
    NOT_FOUND = "not_found"
    CLARIFICATION_NEEDED = "clarification_needed"
    CONFLICTING_SOURCES = "conflicting_sources"


class Category(str, Enum):
    ADMISSION = "admission"
    DEPARTMENT = "department"
    FEES = "fees"
    FACILITIES = "facilities"
    EXAM = "exam"
    CERTIFICATE = "certificate"
    CONTACT = "contact"
    OTHER = "other"


@dataclass
class FAQ:
    id: str
    category: str
    question: str
    keywords: List[str]
    answer: str
    source_name: str
    source_url: Optional[str]
    last_verified: date
    valid_until: Optional[date]
    status: str = "approved"  # approved, draft, deprecated


@dataclass
class Department:
    id: str
    name: str
    short_description: str
    course_duration: str
    hod_name: Optional[str]
    contact: Optional[str]
    facilities: List[str]
    official_source_link: Optional[str]
    last_verified: date


@dataclass
class ContactInfo:
    office_name: str
    phone: Optional[str]
    email: Optional[str]
    location: Optional[str]
    office_hours: Optional[str]


@dataclass
class UnansweredQuery:
    id: str
    question: str
    category_guess: Optional[str]
    asked_at: str  # ISO datetime string
    count: int = 1


@dataclass
class ChatbotResponse:
    answer: str
    status: AnswerStatus
    category: Optional[Category]
    used_source_ids: List[str]
    unsupported_parts: List[str]
    needs_verification: bool
    office_to_contact: Optional[str]
    raw_gemini_response: dict = field(default_factory=dict)