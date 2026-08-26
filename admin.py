# admin.py
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple

from config import VALID_CATEGORIES
from models import FAQ, Department, ContactInfo, UnansweredQuery
from knowledge_base import (
    load_faqs,
    save_faqs,
    get_faq_by_id,
    load_departments,
    save_departments,
    get_department_by_id,
    load_contacts,
    save_contacts,
    load_unanswered_queue,
    save_unanswered_queue,
)
from sorting_algorithms import (
    sort_faqs_by_category_then_question,
    sort_faqs_by_last_verified,
    sort_departments_by_name,
)


# ---------- FAQ admin operations ----------

def _generate_faq_id(faqs: List[FAQ]) -> str:
    existing_ids = {f.id for f in faqs}
    base = "faq_"
    counter = 1
    while True:
        new_id = f"{base}{counter}"
        if new_id not in existing_ids:
            return new_id
        counter += 1


def validate_faq_data(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate FAQ data before creating/updating.
    Returns (is_valid, error_message).
    """
    required_fields = ["category", "question", "answer", "source_name", "last_verified"]
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"

    if data["category"] not in VALID_CATEGORIES:
        return False, f"Invalid category: {data['category']}. Must be one of {VALID_CATEGORIES}"

    # Validate date formats
    for date_field in ["last_verified", "valid_until"]:
        if date_field in data and data[date_field]:
            try:
                if isinstance(data[date_field], str):
                    date.fromisoformat(data[date_field])
            except ValueError:
                return False, f"Invalid date format for {date_field}: use YYYY-MM-DD"

    return True, None


def add_faq(
    category: str,
    question: str,
    answer: str,
    source_name: str,
    last_verified: str,
    keywords: Optional[List[str]] = None,
    source_url: Optional[str] = None,
    valid_until: Optional[str] = None,
    status: str = "approved",
) -> Tuple[bool, Optional[FAQ], Optional[str]]:
    """
    Add a new FAQ.
    Returns (success, faq_object, error_message).
    """
    data = {
        "category": category,
        "question": question,
        "answer": answer,
        "source_name": source_name,
        "last_verified": last_verified,
        "keywords": keywords or [],
        "source_url": source_url,
        "valid_until": valid_until,
        "status": status,
    }

    is_valid, error = validate_faq_data(data)
    if not is_valid:
        return False, None, error

    faqs = load_faqs()
    new_id = _generate_faq_id(faqs)

    new_faq = FAQ(
        id=new_id,
        category=category,
        question=question,
        keywords=keywords or [],
        answer=answer,
        source_name=source_name,
        source_url=source_url,
        last_verified=date.fromisoformat(last_verified) if isinstance(last_verified, str) else last_verified,
        valid_until=date.fromisoformat(valid_until) if valid_until else None,
        status=status,
    )

    faqs.append(new_faq)
    save_faqs(faqs)
    return True, new_faq, None


def update_faq(
    faq_id: str,
    category: Optional[str] = None,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    source_name: Optional[str] = None,
    source_url: Optional[str] = None,
    last_verified: Optional[str] = None,
    valid_until: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[bool, Optional[FAQ], Optional[str]]:
    """
    Update an existing FAQ by ID.
    Only provided fields are updated.
    Returns (success, updated_faq, error_message).
    """
    faqs = load_faqs()
    faq = get_faq_by_id(faq_id, faqs)
    if not faq:
        return False, None, f"FAQ with id {faq_id} not found."

    # Prepare updated data
    data = {
        "category": category or faq.category,
        "question": question or faq.question,
        "answer": answer or faq.answer,
        "keywords": keywords if keywords is not None else faq.keywords,
        "source_name": source_name or faq.source_name,
        "source_url": source_url if source_url is not None else faq.source_url,
        "last_verified": last_verified or faq.last_verified.isoformat(),
        "valid_until": valid_until if valid_until is not None else (faq.valid_until.isoformat() if faq.valid_until else None),
        "status": status or faq.status,
    }

    is_valid, error = validate_faq_data(data)
    if not is_valid:
        return False, None, error

    # Apply updates
    faq.category = data["category"]
    faq.question = data["question"]
    faq.answer = data["answer"]
    faq.keywords = data["keywords"]
    faq.source_name = data["source_name"]
    faq.source_url = data["source_url"]
    faq.last_verified = (
        date.fromisoformat(data["last_verified"])
        if isinstance(data["last_verified"], str)
        else data["last_verified"]
    )
    faq.valid_until = (
        date.fromisoformat(data["valid_until"])
        if data["valid_until"] and isinstance(data["valid_until"], str)
        else data["valid_until"]
    )
    faq.status = data["status"]

    save_faqs(faqs)
    return True, faq, None


def delete_faq(faq_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete an FAQ by ID.
    Returns (success, error_message).
    """
    faqs = load_faqs()
    faq = get_faq_by_id(faq_id, faqs)
    if not faq:
        return False, f"FAQ with id {faq_id} not found."

    faqs = [f for f in faqs if f.id != faq_id]
    save_faqs(faqs)
    return True, None


def list_faqs(
    sort_by: str = "category",
    category_filter: Optional[str] = None,
) -> List[FAQ]:
    """
    List FAQs with optional category filter and sorting.
    sort_by: 'category' or 'last_verified'
    """
    faqs = load_faqs()

    if category_filter:
        faqs = [f for f in faqs if f.category == category_filter]

    if sort_by == "category":
        return sort_faqs_by_category_then_question(faqs, algorithm="bubble")
    elif sort_by == "last_verified":
        return sort_faqs_by_last_verified(faqs, algorithm="bubble", reverse=True)
    else:
        return faqs


# ---------- Department admin operations ----------

def _generate_department_id(departments: List[Department]) -> str:
    existing_ids = {d.id for d in departments}
    base = "dept_"
    counter = 1
    while True:
        new_id = f"{base}{counter}"
        if new_id not in existing_ids:
            return new_id
        counter += 1


def add_department(
    name: str,
    short_description: str,
    course_duration: str,
    hod_name: Optional[str] = None,
    contact: Optional[str] = None,
    facilities: Optional[List[str]] = None,
    official_source_link: Optional[str] = None,
    last_verified: Optional[str] = None,
) -> Tuple[bool, Optional[Department], Optional[str]]:
    """
    Add a new department.
    Returns (success, department_object, error_message).
    """
    if not name or not short_description or not course_duration:
        return False, None, "name, short_description, and course_duration are required."

    departments = load_departments()
    new_id = _generate_department_id(departments)

    last_verified_date = None
    if last_verified:
        try:
            last_verified_date = date.fromisoformat(last_verified)
        except ValueError:
            return False, None, "Invalid last_verified date format. Use YYYY-MM-DD."

    new_dep = Department(
        id=new_id,
        name=name,
        short_description=short_description,
        course_duration=course_duration,
        hod_name=hod_name,
        contact=contact,
        facilities=facilities or [],
        official_source_link=official_source_link,
        last_verified=last_verified_date or date.today(),
    )

    departments.append(new_dep)
    save_departments(departments)
    return True, new_dep, None


def update_department(
    dep_id: str,
    name: Optional[str] = None,
    short_description: Optional[str] = None,
    course_duration: Optional[str] = None,
    hod_name: Optional[str] = None,
    contact: Optional[str] = None,
    facilities: Optional[List[str]] = None,
    official_source_link: Optional[str] = None,
    last_verified: Optional[str] = None,
) -> Tuple[bool, Optional[Department], Optional[str]]:
    """
    Update an existing department by ID.
    Returns (success, updated_department, error_message).
    """
    departments = load_departments()
    dep = get_department_by_id(dep_id, departments)
    if not dep:
        return False, None, f"Department with id {dep_id} not found."

    if name:
        dep.name = name
    if short_description:
        dep.short_description = short_description
    if course_duration:
        dep.course_duration = course_duration
    if hod_name is not None:
        dep.hod_name = hod_name
    if contact is not None:
        dep.contact = contact
    if facilities is not None:
        dep.facilities = facilities
    if official_source_link is not None:
        dep.official_source_link = official_source_link
    if last_verified:
        try:
            dep.last_verified = date.fromisoformat(last_verified)
        except ValueError:
            return False, None, "Invalid last_verified date format. Use YYYY-MM-DD."

    save_departments(departments)
    return True, dep, None


def list_departments(sort_by: str = "name") -> List[Department]:
    """
    List all departments, optionally sorted.
    sort_by: 'name'
    """
    departments = load_departments()
    if sort_by == "name":
        return sort_departments_by_name(departments, algorithm="bubble")
    return departments


# ---------- Contact admin operations ----------

def add_contact(
    office_name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    location: Optional[str] = None,
    office_hours: Optional[str] = None,
) -> Tuple[bool, Optional[ContactInfo], Optional[str]]:
    """
    Add a new contact entry.
    Returns (success, contact_object, error_message).
    """
    if not office_name:
        return False, None, "office_name is required."

    contacts = load_contacts()
    new_contact = ContactInfo(
        office_name=office_name,
        phone=phone,
        email=email,
        location=location,
        office_hours=office_hours,
    )

    contacts.append(new_contact)
    save_contacts(contacts)
    return True, new_contact, None


def list_contacts() -> List[ContactInfo]:
    """
    List all contact entries.
    """
    return load_contacts()


# ---------- Unanswered queue admin operations ----------

def list_unanswered_questions() -> List[UnansweredQuery]:
    """
    List all unanswered questions, sorted by count descending.
    """
    queue = load_unanswered_queue()
    queue.sort(key=lambda q: q.count, reverse=True)
    return queue


def clear_unanswered_question(uq_id: str) -> Tuple[bool, Optional[str]]:
    """
    Remove an unanswered question from the queue.
    Returns (success, error_message).
    """
    queue = load_unanswered_queue()
    initial_len = len(queue)
    queue = [q for q in queue if q.id != uq_id]

    if len(queue) == initial_len:
        return False, f"Unanswered question with id {uq_id} not found."

    save_unanswered_queue(queue)
    return True, None


def clear_all_unanswered_questions() -> None:
    """
    Clear the entire unanswered queue.
    """
    save_unanswered_queue([])