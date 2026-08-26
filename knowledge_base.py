# knowledge_base.py
import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from config import (
    FAQ_JSON_PATH,
    DEPARTMENTS_JSON_PATH,
    CONTACTS_JSON_PATH,
    UNANSWERED_QUEUE_JSON_PATH,
    VALID_CATEGORIES,
)
from models import FAQ, Department, ContactInfo, UnansweredQuery


def _load_json(path: Path) -> Any:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, "%Y-%m-%d").date()


def _serialize_date(d: Optional[date]) -> Optional[str]:
    if d is None:
        return None
    return d.isoformat()


# ---------- FAQ operations ----------

def load_faqs() -> List[FAQ]:
    raw = _load_json(FAQ_JSON_PATH)
    faqs = []
    for r in raw:
        faqs.append(
            FAQ(
                id=r["id"],
                category=r["category"],
                question=r["question"],
                keywords=r.get("keywords", []),
                answer=r["answer"],
                source_name=r.get("source_name", ""),
                source_url=r.get("source_url"),
                last_verified=_parse_date(r.get("last_verified")),
                valid_until=_parse_date(r.get("valid_until")),
                status=r.get("status", "approved"),
            )
        )
    return faqs


def save_faqs(faqs: List[FAQ]) -> None:
    raw = []
    for f in faqs:
        raw.append(
            {
                "id": f.id,
                "category": f.category,
                "question": f.question,
                "keywords": f.keywords,
                "answer": f.answer,
                "source_name": f.source_name,
                "source_url": f.source_url,
                "last_verified": _serialize_date(f.last_verified),
                "valid_until": _serialize_date(f.valid_until),
                "status": f.status,
            }
        )
    _save_json(FAQ_JSON_PATH, raw)


def get_faq_by_id(faq_id: str, faqs: List[FAQ]) -> Optional[FAQ]:
    for f in faqs:
        if f.id == faq_id:
            return f
    return None


def filter_faqs_by_category(category: str, faqs: List[FAQ]) -> List[FAQ]:
    if category not in VALID_CATEGORIES:
        return []
    return [f for f in faqs if f.category == category]


# ---------- Department operations ----------

def load_departments() -> List[Department]:
    raw = _load_json(DEPARTMENTS_JSON_PATH)
    deps = []
    for r in raw:
        deps.append(
            Department(
                id=r["id"],
                name=r["name"],
                short_description=r.get("short_description", ""),
                course_duration=r.get("course_duration", ""),
                hod_name=r.get("hod_name"),
                contact=r.get("contact"),
                facilities=r.get("facilities", []),
                official_source_link=r.get("official_source_link"),
                last_verified=_parse_date(r.get("last_verified")),
            )
        )
    return deps


def save_departments(departments: List[Department]) -> None:
    raw = []
    for d in departments:
        raw.append(
            {
                "id": d.id,
                "name": d.name,
                "short_description": d.short_description,
                "course_duration": d.course_duration,
                "hod_name": d.hod_name,
                "contact": d.contact,
                "facilities": d.facilities,
                "official_source_link": d.official_source_link,
                "last_verified": _serialize_date(d.last_verified),
            }
        )
    _save_json(DEPARTMENTS_JSON_PATH, raw)


def get_department_by_id(dep_id: str, departments: List[Department]) -> Optional[Department]:
    for d in departments:
        if d.id == dep_id:
            return d
    return None


# ---------- Contact operations ----------

def load_contacts() -> List[ContactInfo]:
    raw = _load_json(CONTACTS_JSON_PATH)
    contacts = []
    for r in raw:
        contacts.append(
            ContactInfo(
                office_name=r["office_name"],
                phone=r.get("phone"),
                email=r.get("email"),
                location=r.get("location"),
                office_hours=r.get("office_hours"),
            )
        )
    return contacts


def save_contacts(contacts: List[ContactInfo]) -> None:
    raw = []
    for c in contacts:
        raw.append(
            {
                "office_name": c.office_name,
                "phone": c.phone,
                "email": c.email,
                "location": c.location,
                "office_hours": c.office_hours,
            }
        )
    _save_json(CONTACTS_JSON_PATH, raw)


def get_contact_by_office_name(office_name: str, contacts: List[ContactInfo]) -> Optional[ContactInfo]:
    name_lower = office_name.lower()
    for c in contacts:
        if name_lower in c.office_name.lower():
            return c
    return None


# ---------- Unanswered query operations ----------

def load_unanswered_queue() -> List[UnansweredQuery]:
    raw = _load_json(UNANSWERED_QUEUE_JSON_PATH)
    queue = []
    for r in raw:
        queue.append(
            UnansweredQuery(
                id=r["id"],
                question=r["question"],
                category_guess=r.get("category_guess"),
                asked_at=r["asked_at"],
                count=r.get("count", 1),
            )
        )
    return queue


def save_unanswered_queue(queue: List[UnansweredQuery]) -> None:
    raw = []
    for q in queue:
        raw.append(
            {
                "id": q.id,
                "question": q.question,
                "category_guess": q.category_guess,
                "asked_at": q.asked_at,
                "count": q.count,
            }
        )
    _save_json(UNANSWERED_QUEUE_JSON_PATH, raw)


def add_or_increment_unanswered_question(
    question: str,
    category_guess: Optional[str],
    queue: List[UnansweredQuery],
) -> List[UnansweredQuery]:
    q_lower = question.strip().lower()
    for item in queue:
        if item.question.lower() == q_lower:
            item.count += 1
            return queue

    new_item = UnansweredQuery(
        id=f"uq_{len(queue) + 1}",
        question=question.strip(),
        category_guess=category_guess,
        asked_at=datetime.now().isoformat(),
        count=1,
    )
    queue.append(new_item)
    return queue