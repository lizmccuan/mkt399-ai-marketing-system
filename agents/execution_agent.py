"""Execution Agent."""

from __future__ import annotations


def run_execution_agent(strategy: dict[str, object]) -> dict[str, object]:
    """Convert strategy recommendations into human-ready marketing assets."""
    strategy_data = strategy["strategy"]
    primary_query = strategy_data["primary_query"]["query"]
    secondary_query = strategy_data["secondary_query"]["query"]
    primary_page = strategy_data["primary_page"]
    semrush_topic = strategy_data.get("next_best_content_topic")
    support_topic = pick_support_topic(primary_query, secondary_query, semrush_topic)

    internal_link_suggestions = [
        "Migraine quiz",
        f"Main treatment page: {primary_page}",
        "Contact or booking page",
    ]

    blog_content_draft = {
        "asset_type": "blog_content_draft",
        "title": f"{primary_query.title()}: what patients in Evergreen Park should know about cost, savings, and next steps",
        "target_query": primary_query,
        "search_intent": "High-intent informational with conversion potential",
        "word_count_target": "500-800 words",
        "draft": build_blog_draft(primary_query, primary_page, support_topic),
        "cta": "Book a consultation, take the migraine quiz, or schedule an appointment to get personalized cost guidance.",
        "internal_link_suggestions": internal_link_suggestions,
    }

    landing_page_refresh_outline = {
        "asset_type": "seo_landing_page_refresh_outline",
        "page_to_refresh": primary_page,
        "primary_keyword": primary_query,
        "recommended_sections": [
            f"Hero section: lead with {primary_query} and mention Evergreen Park and the Chicago suburbs in a natural way.",
            "Savings and affordability section: explain what affects cost, when savings options may apply, and why delaying care can make decisions harder.",
            "Candidate section: describe who may benefit, what local patients often ask, and when it is time to schedule.",
            "Trust section: highlight specialist expertise, local accessibility, and what happens at the first appointment.",
            f"FAQ section: answer direct questions about {primary_query} and {support_topic}.",
            "CTA section: place a strong book-now CTA above the fold and repeat it after the FAQ.",
            "Internal links: point readers to the migraine quiz, the main treatment page, and the booking page.",
        ],
        "meta_title_idea": f"{primary_query.title()} in Evergreen Park | {primary_page}",
        "meta_description_idea": (
            f"Learn about {primary_query}, savings options, and how to book with {primary_page} in Evergreen Park."
        ),
    }

    faq_block = {
        "asset_type": "faq_block",
        "heading": f"Frequently asked questions about {primary_query}",
        "questions": [
            {
                "question": f"How much does {primary_query} usually cost?",
                "answer": (
                    f"If you have been searching for {primary_query} in Evergreen Park or the Chicago suburbs, you probably want a clear answer without the runaround. "
                    "The total cost can vary based on the treatment plan, the number of visits involved, and whether follow-up care is part of the process. "
                    "Instead of relying on generic price ranges online, the best next step is to schedule a consultation and get guidance based on your symptoms and treatment goals."
                ),
            },
            {
                "question": "Are there ways to save money or reduce out-of-pocket costs?",
                "answer": (
                    "Yes. If you have been searching for Botox cost or savings options, there may be ways to reduce out-of-pocket expenses through insurance benefits, timing your care around plan details, or asking whether any savings programs are available. "
                    "If you have been delaying care because cost feels unclear, you do not need to figure this out alone. A quick conversation with the office can help you understand what may apply before you decide to wait any longer."
                ),
            },
            {
                "question": "How do I know if I am a good candidate for treatment?",
                "answer": (
                    "A good candidate is usually someone whose symptoms are frequent, disruptive, or still interfering with work, family time, or daily routines despite basic care. "
                    "If you are looking for a migraine specialist in Evergreen Park or nearby Chicago suburbs, that usually means you want more than information. "
                    "You want a practical answer about whether treatment fits your needs, and that is exactly where a specialist consultation can help."
                ),
            },
            {
                "question": "What should I do if I am comparing clinics and still unsure?",
                "answer": (
                    f"If you are still comparing options, focus on whether the provider explains cost clearly, connects treatment to your symptoms, and makes the next step easy. "
                    f"{primary_page} should guide you toward a migraine quiz, the main treatment page, and a clear booking option so you can move from research to action. "
                    "If you have been putting this off, now is a good time to schedule and get real answers instead of continuing to sort through generic advice."
                ),
            },
        ],
    }

    social_post_draft = {
        "asset_type": "social_post_draft",
        "platform": "Facebook",
        "goal": "Drive high-intent local patients to a cost-and-savings-focused service page.",
        "copy": (
            f"If you have been searching for Botox cost or savings options in Evergreen Park or the Chicago suburbs, you are probably ready for clearer answers. "
            f"Our updated {primary_page} is built for people who want to understand {primary_query}, what may affect cost, and when it makes sense to stop waiting and book a visit. "
            "If you have been delaying care because the process feels confusing, you do not need to figure it out alone. Take the migraine quiz, review your treatment options, and schedule your appointment today."
        ),
    }

    execution_plan = [
        blog_content_draft,
        landing_page_refresh_outline,
        faq_block,
        social_post_draft,
    ]

    print("[Execution Agent] Created full marketing asset package")

    return {
        "agent": "execution",
        "input_agent": strategy["agent"],
        "execution_plan": execution_plan,
        "blog_content_draft": blog_content_draft,
        "landing_page_refresh_outline": landing_page_refresh_outline,
        "faq_block": faq_block,
        "social_post_draft": social_post_draft,
        "internal_link_suggestions": internal_link_suggestions,
        "source_recommendations": strategy_data["recommendations"],
        "best_practice_context": extract_best_practices(strategy_data["recommendations"]),
        "notes": [
            "Execution Agent converts structured strategy into real marketing assets.",
            "Outputs are grounded in SEO, AEO/GEO, UX, and content best practices.",
        ],
    }


def extract_best_practices(recommendations: dict) -> list[str]:
    """Extract unique best-practice categories from strategy recommendations."""
    categories = set()

    for section in recommendations.values():
        for item in section:
            category = item.get("best_practice_category")
            if category:
                categories.add(category)

    return list(categories)


def build_blog_draft(primary_query: str, primary_page: str, support_topic: str) -> str:
    """Write a human-ready blog draft."""
    return (
        f"If you have been searching for {primary_query}, you are probably looking for real answers, not generic advice. "
        f"This guide helps patients in Evergreen Park understand cost, options, and next steps.\n\n"
        f"{primary_query} is often searched by people comparing providers, evaluating affordability, and deciding whether to move forward.\n\n"
        f"If you have also searched for {support_topic}, your concern is not just cost — it is whether there is a realistic path forward.\n\n"
        f"This content connects directly to {primary_page}, guiding you from research to action.\n\n"
        "Take the migraine quiz, review treatment options, and schedule your consultation to get personalized guidance."
    )


def pick_support_topic(
    primary_query: str,
    secondary_query: str,
    semrush_topic: dict[str, object] | None = None,
) -> str:
    """Choose supporting topic."""
    if semrush_topic and semrush_topic.get("topic"):
        return str(semrush_topic["topic"])
    if "savings" in primary_query.lower():
        return "botox savings"
    if "cost" in primary_query.lower():
        return "botox savings"
    return secondary_query
