# sorting_algorithms.py
from typing import List, Callable, Any
from models import FAQ, Department


# ---------- Generic sorting helpers ----------

def bubble_sort(
    arr: List[Any],
    key: Callable[[Any], Any],
    reverse: bool = False,
) -> List[Any]:
    """
    Classic bubble sort implementation.
    Sorts based on the provided key function.
    """
    n = len(arr)
    a = arr[:]  # work on a copy

    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if (key(a[j]) > key(a[j + 1])) != reverse:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a


def insertion_sort(
    arr: List[Any],
    key: Callable[[Any], Any],
    reverse: bool = False,
) -> List[Any]:
    """
    Classic insertion sort implementation.
    Sorts based on the provided key function.
    """
    a = arr[:]  # work on a copy

    for i in range(1, len(a)):
        current = a[i]
        current_key = key(current)
        j = i - 1

        while j >= 0 and ((key(a[j]) > current_key) != reverse):
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = current

    return a


# ---------- FAQ-specific sorting ----------

def sort_faqs_by_question(
    faqs: List[FAQ],
    algorithm: str = "bubble",
    reverse: bool = False,
) -> List[FAQ]:
    """
    Sort FAQs by normalized question text.
    algorithm: 'bubble' or 'insertion'
    """
    from search_algorithms import normalize_text

    def key_func(faq: FAQ) -> str:
        return normalize_text(faq.question)

    if algorithm == "bubble":
        return bubble_sort(faqs, key_func, reverse=reverse)
    elif algorithm == "insertion":
        return insertion_sort(faqs, key_func, reverse=reverse)
    else:
        raise ValueError("algorithm must be 'bubble' or 'insertion'")


def sort_faqs_by_category_then_question(
    faqs: List[FAQ],
    algorithm: str = "bubble",
    reverse: bool = False,
) -> List[FAQ]:
    """
    Sort FAQs by (category, question) tuple.
    Useful for grouped display: all admission FAQs together, etc.
    """
    from search_algorithms import normalize_text

    def key_func(faq: FAQ) -> tuple[str, str]:
        return (faq.category.lower(), normalize_text(faq.question))

    if algorithm == "bubble":
        return bubble_sort(faqs, key_func, reverse=reverse)
    elif algorithm == "insertion":
        return insertion_sort(faqs, key_func, reverse=reverse)
    else:
        raise ValueError("algorithm must be 'bubble' or 'insertion'")


def sort_faqs_by_last_verified(
    faqs: List[FAQ],
    algorithm: str = "bubble",
    reverse: bool = False,
) -> List[FAQ]:
    """
    Sort FAQs by last_verified date.
    reverse=False → oldest first
    reverse=True  → newest first
    """
    def key_func(faq: FAQ):
        # Treat None as very old date
        return faq.last_verified or type(faq.last_verified).min

    if algorithm == "bubble":
        return bubble_sort(faqs, key_func, reverse=reverse)
    elif algorithm == "insertion":
        return insertion_sort(faqs, key_func, reverse=reverse)
    else:
        raise ValueError("algorithm must be 'bubble' or 'insertion'")


# ---------- Department-specific sorting ----------

def sort_departments_by_name(
    departments: List[Department],
    algorithm: str = "bubble",
    reverse: bool = False,
) -> List[Department]:
    """
    Sort departments by name (case-insensitive).
    """
    def key_func(dep: Department) -> str:
        return dep.name.lower()

    if algorithm == "bubble":
        return bubble_sort(departments, key_func, reverse=reverse)
    elif algorithm == "insertion":
        return insertion_sort(departments, key_func, reverse=reverse)
    else:
        raise ValueError("algorithm must be 'bubble' or 'insertion'")