# chatbot_engine.py
from typing import List, Dict, Any, Optional, Tuple
from datetime import date

from config import MIN_GROUNDING_SOURCE_COUNT
from models import ChatbotResponse, AnswerStatus, FAQ, Category
from knowledge_base import (
    load_faqs,
    load_departments,
    load_contacts,
    load_unanswered_queue,
    save_unanswered_queue,
    add_or_increment_unanswered_question,
)
from search_algorithms import (
    rank_faqs_by_relevance,
    linear_search_faqs_by_category,
    normalize_text,
    extract_keywords,
)
from gemini_client import call_gemini_for_answer


def _build_context_from_faqs(
    question: str,
    faqs: List[FAQ],
    top_k: int = 5,
) -> Tuple[List[Dict[str, Any]], List[FAQ]]:
    """
    Retrieve top-k relevant FAQs and convert them into context dicts
    suitable for Gemini.
    Returns (context_list, matched_faqs).
    """
    ranked = rank_faqs_by_relevance(question, faqs, top_k=top_k)
    context = []
    matched_faqs = []

    for faq, score in ranked:
        if score <= 0:
            continue

        doc = {
            "id": faq.id,
            "title": f"FAQ: {faq.question}",
            "content": faq.answer,
            "last_verified": faq.last_verified.isoformat() if faq.last_verified else "",
            "source_name": faq.source_name,
            "category": faq.category,
        }
        context.append(doc)
        matched_faqs.append(faq)

    return context, matched_faqs


def _build_department_context(
    question: str,
    departments: List[Any],  # List[Department]
) -> List[Dict[str, Any]]:
    """
    If the question seems department-related, build context from departments.
    Simple heuristic: if any department name appears in the question.
    """
    context = []
    q_lower = question.lower()

    for dep in departments:
        if dep.name.lower() in q_lower:
            doc = {
                "id": f"dept_{dep.id}",
                "title": f"Department: {dep.name}",
                "content": (
                    f"{dep.short_description} "
                    f"Course duration: {dep.course_duration}. "
                    f"HOD: {dep.hod_name or 'N/A'}. "
                    f"Contact: {dep.contact or 'N/A'}. "
                    f"Facilities: {', '.join(dep.facilities)}."
                ),
                "last_verified": dep.last_verified.isoformat() if dep.last_verified else "",
                "source_name": dep.official_source_link or "College website",
                "category": "department",
            }
            context.append(doc)

    return context


def _build_contact_context(
    question: str,
    contacts: List[Any],  # List[ContactInfo]
) -> List[Dict[str, Any]]:
    """
    If the question mentions an office name, include that contact info.
    """
    context = []
    q_lower = question.lower()

    for c in contacts:
        if c.office_name.lower() in q_lower:
            doc = {
                "id": f"contact_{c.office_name}",
                "title": f"Contact: {c.office_name}",
                "content": (
                    f"Office: {c.office_name}. "
                    f"Phone: {c.phone or 'N/A'}. "
                    f"Email: {c.email or 'N/A'}. "
                    f"Location: {c.location or 'N/A'}. "
                    f"Office hours: {c.office_hours or 'N/A'}."
                ),
                "last_verified": "",
                "source_name": "College contact list",
                "category": "contact",
            }
            context.append(doc)

    return context


def _infer_category_from_question(question: str, faqs: List[FAQ]) -> Optional[Category]:
    """
    Simple heuristic category inference based on keyword overlap with FAQs.
    """
    q_keywords = set(extract_keywords(question))
    category_scores = {cat: 0 for cat in [c.value for c in Category]}

    for faq in faqs:
        if faq.status != "approved":
            continue
        f_keywords = set(extract_keywords(faq.question + " " + " ".join(faq.keywords)))
        overlap = len(q_keywords & f_keywords)
        if overlap > 0:
            category_scores[faq.category] += overlap

    best_cat = max(category_scores, key=category_scores.get)
    if category_scores[best_cat] > 0:
        try:
            return Category(best_cat)
        except ValueError:
            return None
    return None


def _create_fallback_response(
    question: str,
    inferred_category: Optional[Category],
) -> ChatbotResponse:
    """
    Create a safe fallback response when no grounded answer is available.
    """
    office_map = {
        Category.ADMISSION: "Admission Office",
        Category.FEES: "Accounts / Fee Section",
        Category.DEPARTMENT: "Respective Department Office",
        Category.EXAM: "Examination Cell",
        Category.CERTIFICATE: "Student Section",
        Category.FACILITIES: "Admin Office",
        Category.CONTACT: "Admin Office",
        Category.OTHER: "Admin Office",
    }

    office = office_map.get(inferred_category, "Admin Office") if inferred_category else "Admin Office"

    return ChatbotResponse(
        answer=(
            "I do not have verified information for that in the current knowledge base. "
            f"Please contact the {office} for confirmation."
        ),
        status=AnswerStatus.NOT_FOUND,
        category=inferred_category,
        used_source_ids=[],
        unsupported_parts=[question],
        needs_verification=False,
        office_to_contact=office,
        raw_gemini_response={},
    )


def process_student_question(
    question: str,
    use_gemini: bool = True,
) -> ChatbotResponse:
    """
    Main entry point for processing a student's question.

    Steps:
    1. Load FAQs, departments, contacts.
    2. Retrieve relevant context (FAQs, departments, contacts).
    3. If use_gemini=True and context is non-empty, call Gemini.
    4. Validate Gemini response (grounding, sources, unsupported parts).
    5. If validation fails or context is empty, return a safe fallback.
    6. Optionally log unanswered questions.
    """
    faqs = load_faqs()
    departments = load_departments()
    contacts = load_contacts()

    # Retrieve context
    faq_context, matched_faqs = _build_context_from_faqs(question, faqs, top_k=5)
    dept_context = _build_department_context(question, departments)
    contact_context = _build_contact_context(question, contacts)

    all_context = faq_context + dept_context + contact_context
    inferred_category = _infer_category_from_question(question, faqs)

    # If no context found, return fallback immediately
    if not all_context:
        return _create_fallback_response(question, inferred_category)

    if not use_gemini:
        # Fallback to top FAQ answer directly
        if matched_faqs:
            top_faq = matched_faqs[0]
            return ChatbotResponse(
                answer=top_faq.answer,
                status=AnswerStatus.GROUNDED,
                category=Category(top_faq.category),
                used_source_ids=[top_faq.id],
                unsupported_parts=[],
                needs_verification=False,
                office_to_contact=None,
                raw_gemini_response={"source": "local_faq"},
            )
        else:
            return _create_fallback_response(question, inferred_category)

    # Call Gemini with retrieved context
    try:
        gemini_response = call_gemini_for_answer(question, all_context)
    except Exception as e:
        # On any error, fallback safely
        return _create_fallback_response(question, inferred_category)

    # Validation rules
    # 1. If status is not grounded, use fallback or clarification
    if gemini_response.status != AnswerStatus.GROUNDED:
        if gemini_response.status == AnswerStatus.CLARIFICATION_NEEDED:
            # Return clarification question directly
            return gemini_response
        else:
            return _create_fallback_response(question, inferred_category)

    # 2. If no sources used, treat as not grounded
    if len(gemini_response.used_source_ids) < MIN_GROUNDING_SOURCE_COUNT:
        return _create_fallback_response(question, inferred_category)

    # 3. If there are unsupported parts for a critical question, still show answer
    # but mark needs_verification = True
    if gemini_response.unsupported_parts:
        gemini_response.needs_verification = True

    return gemini_response


def add_unanswered_question_if_needed(response: ChatbotResponse, question: str) -> None:
    """
    If the response is not grounded, add/increment the question in the unresolved queue.
    """
    if response.status in (AnswerStatus.GROUNDED,):
        return

    queue = load_unanswered_queue()
    updated_queue = add_or_increment_unanswered_question(
        question=question,
        category_guess=response.category.value if response.category else None,
        queue=queue,
    )
    save_unanswered_queue(updated_queue)