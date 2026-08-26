# main.py
import sys
from typing import Optional

from chatbot_engine import process_student_question, add_unanswered_question_if_needed
from admin import (
    list_faqs,
    add_faq,
    list_unanswered_questions,
    clear_unanswered_question,
)
from config import VALID_CATEGORIES


def print_welcome() -> None:
    print("\n=== PolyGuide: Polytechnic College Information Chatbot (CLI) ===")
    print("Type your question about the college (admission, courses, departments, etc.).")
    print("Commands:")
    print("  list-faqs [category]   - List FAQs (optionally filtered by category)")
    print("  add-faq                - Add a new FAQ (admin)")
    print("  unanswered             - List unanswered questions (admin)")
    print("  clear-uq <id>          - Clear an unanswered question by ID")
    print("  exit                   - Exit the chatbot")
    print("=" * 60)


def handle_list_faqs(args: list[str]) -> None:
    category = args[0] if args else None
    if category and category not in VALID_CATEGORIES:
        print(f"Invalid category. Choose from: {', '.join(sorted(VALID_CATEGORIES))}")
        return

    faqs = list_faqs(sort_by="category", category_filter=category)
    if not faqs:
        print("No FAQs found.")
        return

    print(f"\n--- FAQs (total: {len(faqs)}) ---")
    for i, f in enumerate(faqs, start=1):
        print(f"{i}. [{f.category}] {f.question}")
        print(f"   Answer: {f.answer[:120]}{'...' if len(f.answer) > 120 else ''}")
        print(f"   Source: {f.source_name} | Verified: {f.last_verified}")
        print()


def handle_add_faq() -> None:
    print("\n--- Add New FAQ ---")
    print(f"Valid categories: {', '.join(sorted(VALID_CATEGORIES))}")

    category = input("Category: ").strip().lower()
    if category not in VALID_CATEGORIES:
        print("Invalid category.")
        return

    question = input("Question: ").strip()
    answer = input("Answer: ").strip()
    source_name = input("Source name (e.g., 'Admission Notice 2026'): ").strip()
    last_verified = input("Last verified (YYYY-MM-DD): ").strip()

    keywords_raw = input("Keywords (comma-separated, optional): ").strip()
    keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()] if keywords_raw else []

    source_url = input("Source URL (optional): ").strip() or None
    valid_until = input("Valid until (YYYY-MM-DD, optional): ").strip() or None

    success, faq, error = add_faq(
        category=category,
        question=question,
        answer=answer,
        source_name=source_name,
        last_verified=last_verified,
        keywords=keywords,
        source_url=source_url,
        valid_until=valid_until,
        status="approved",
    )

    if success:
        print("\nFAQ added successfully.")
        print(f"ID: {faq.id}")
        print(f"Q: {faq.question}")
        print(f"A: {faq.answer}")
    else:
        print(f"\nFailed to add FAQ: {error}")


def handle_unanswered() -> None:
    queue = list_unanswered_questions()
    if not queue:
        print("\nNo unanswered questions in the queue.")
        return

    print("\n--- Unanswered Questions ---")
    for q in queue:
        print(f"[{q.id}] (count: {q.count}, category: {q.category_guess or 'unknown'})")
        print(f"  Question: {q.question}")
        print(f"  Asked at: {q.asked_at}")
        print()


def handle_clear_uq(uq_id: str) -> None:
    success, error = clear_unanswered_question(uq_id)
    if success:
        print(f"\nUnanswered question {uq_id} cleared.")
    else:
        print(f"\nFailed to clear unanswered question: {error}")


def process_command(line: str) -> Optional[bool]:
    """
    Process a command line.
    Returns True if should exit, False if continue, None if not a command.
    """
    parts = line.strip().split()
    if not parts:
        return None

    cmd = parts[0].lower()

    if cmd == "exit":
        return True

    if cmd == "list-faqs":
        handle_list_faqs(parts[1:])
        return False

    if cmd == "add-faq":
        handle_add_faq()
        return False

    if cmd == "unanswered":
        handle_unanswered()
        return False

    if cmd == "clear-uq":
        if len(parts) < 2:
            print("Usage: clear-uq <id>")
        else:
            handle_clear_uq(parts[1])
        return False

    return None


def run_chatbot() -> None:
    print_welcome()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chatbot.")
            break

        if not user_input:
            continue

        should_exit = process_command(user_input)
        if should_exit is True:
            print("Goodbye!")
            break
        if should_exit is False:
            continue

        # Treat as a student question
        print("\nBot: Processing your question...")

        try:
            response = process_student_question(user_input, use_gemini=True)
        except Exception as e:
            print(f"Bot: Error while processing question: {e}")
            continue

        # Show answer
        print("\n--- Answer ---")
        print(response.answer)

        if response.category:
            print(f"Category: {response.category.value}")

        if response.used_source_ids:
            print(f"Sources used: {', '.join(response.used_source_ids)}")

        if response.unsupported_parts:
            print(f"Unsupported parts: {', '.join(response.unsupported_parts)}")

        if response.needs_verification:
            print(
                "⚠️  This information may be time-sensitive. "
                "Please verify current details with the concerned college office."
            )

        if response.office_to_contact and response.status.name != "GROUNDED":
            print(f"Suggested contact: {response.office_to_contact}")

        # Log unanswered if needed
        try:
            add_unanswered_question_if_needed(response, user_input)
        except Exception as e:
            # Do not break the chatbot for logging errors
            print(f"[Warning] Failed to log unanswered question: {e}")


if __name__ == "__main__":
    run_chatbot()