# search_algorithms.py
from typing import List, Optional, Tuple, Dict, Any
from models import FAQ


def normalize_text(text: str) -> str:
    """
    Normalize text for search:
    - lowercase
    - strip extra spaces
    - remove common punctuation
    """
    import re
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = " ".join(text.split())
    return text


def extract_keywords(question: str) -> List[str]:
    """
    Extract simple keywords from a question.
    Removes stopwords and returns meaningful tokens.
    """
    stopwords = {
        "what", "is", "are", "the", "a", "an", "how", "to", "for",
        "in", "of", "and", "or", "can", "i", "we", "you", "they",
        "do", "does", "did", "have", "has", "had", "will", "would",
        "could", "should", "may", "might", "about", "with", "on",
        "at", "from", "by", "as", "be", "been", "being", "my", "our",
        "their", "its", "this", "that", "these", "those", "which",
        "who", "whom", "whose", "when", "where", "why", "if", "then",
        "else", "but", "so", "just", "also", "only", "very", "really",
    }
    normalized = normalize_text(question)
    words = normalized.split()
    return [w for w in words if w not in stopwords and len(w) > 1]


def linear_search_faqs_by_question(
    question: str,
    faqs: List[FAQ],
) -> List[Tuple[FAQ, int]]:
    """
    Linear search over FAQs based on keyword overlap with the question.
    Returns a list of (FAQ, score) sorted by score descending.
    """
    q_keywords = extract_keywords(question)
    results: List[Tuple[FAQ, int]] = []

    for faq in faqs:
        if faq.status != "approved":
            continue

        # Combine question and keywords for matching
        text = normalize_text(faq.question + " " + " ".join(faq.keywords))
        f_words = set(text.split())

        score = sum(1 for kw in q_keywords if kw in f_words)
        if score > 0:
            results.append((faq, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def linear_search_faqs_by_category(
    category: str,
    faqs: List[FAQ],
) -> List[FAQ]:
    """
    Linear search to get all approved FAQs in a given category.
    """
    return [
        f for f in faqs
        if f.category.lower() == category.lower() and f.status == "approved"
    ]


def binary_search_faqs_by_question(
    question: str,
    sorted_faqs: List[FAQ],
) -> Optional[FAQ]:
    """
    Binary search over FAQs sorted by normalized question text.
    Returns the first FAQ whose normalized question exactly matches.
    In practice, this is useful when you maintain a sorted FAQ list
    and want exact/near-exact matches.
    """
    normalized_q = normalize_text(question)

    left, right = 0, len(sorted_faqs) - 1
    while left <= right:
        mid = (left + right) // 2
        faq = sorted_faqs[mid]
        normalized_faq_q = normalize_text(faq.question)

        if normalized_faq_q == normalized_q:
            return faq
        elif normalized_faq_q < normalized_q:
            left = mid + 1
        else:
            right = mid - 1

    return None


def binary_search_faqs_by_category(
    category: str,
    sorted_faqs: List[FAQ],
) -> List[FAQ]:
    """
    Binary search to find the range of FAQs in a given category,
    assuming sorted_faqs is sorted by (category, question).
    Returns all matching FAQs in that category.
    """
    category = category.lower()

    # Find left bound
    left, right = 0, len(sorted_faqs) - 1
    left_idx = -1
    while left <= right:
        mid = (left + right) // 2
        if sorted_faqs[mid].category.lower() >= category:
            left_idx = mid
            right = mid - 1
        else:
            left = mid + 1

    if left_idx == -1 or sorted_faqs[left_idx].category.lower() != category:
        return []

    # Find right bound
    left, right = left_idx, len(sorted_faqs) - 1
    right_idx = -1
    while left <= right:
        mid = (left + right) // 2
        if sorted_faqs[mid].category.lower() <= category:
            right_idx = mid
            left = mid + 1
        else:
            right = mid - 1

    return sorted_faqs[left_idx : right_idx + 1]


def rank_faqs_by_relevance(
    question: str,
    faqs: List[FAQ],
    top_k: int = 5,
) -> List[Tuple[FAQ, float]]:
    """
    Rank FAQs by a simple relevance score:
    - keyword overlap
    - bonus for category match (if inferred)
    Returns top_k (FAQ, score) pairs.
    """
    q_keywords = extract_keywords(question)
    scored: List[Tuple[FAQ, float]] = []

    for faq in faqs:
        if faq.status != "approved":
            continue

        text = normalize_text(faq.question + " " + " ".join(faq.keywords))
        f_words = set(text.split())

        base_score = sum(1 for kw in q_keywords if kw in f_words)
        if base_score == 0:
            continue

        # Simple bonus: if any keyword appears in FAQ question directly
        question_words = set(normalize_text(faq.question).split())
        bonus = sum(1 for kw in q_keywords if kw in question_words)

        total_score = base_score + 0.5 * bonus
        scored.append((faq, total_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]