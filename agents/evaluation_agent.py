"""Evaluation Agent."""

from __future__ import annotations


PLACEHOLDER_MARKERS = [
    "this section should",
    "the page should",
    "the content should",
    "this answer should",
    "a strong page should",
    "placeholder",
]


def run_evaluation_agent(execution: dict[str, object]) -> dict[str, object]:
    """Review the execution output and return a stricter readiness score."""
    strengths = []
    improvements = []

    blog_draft = execution.get("blog_content_draft", {})
    landing_outline = execution.get("landing_page_refresh_outline", {})
    faq_block = execution.get("faq_block", {})
    social_post = execution.get("social_post_draft", {})

    blog_text = blog_draft.get("draft", "")
    faq_answers = " ".join(question.get("answer", "") for question in faq_block.get("questions", []))
    social_text = social_post.get("copy", "")
    combined_text = " ".join([blog_text, faq_answers, social_text]).lower()

    has_placeholders = any(marker in combined_text for marker in PLACEHOLDER_MARKERS)
    blog_word_count = len(blog_text.split())
    fully_written = blog_word_count >= 500 and len(faq_block.get("questions", [])) >= 3 and len(social_text.split()) >= 40
    landing_specific = landing_outline.get("page_to_refresh") and len(landing_outline.get("recommended_sections", [])) >= 5
    has_local_language = "evergreen park" in combined_text and "chicago suburbs" in combined_text
    has_conversion_language = any(
        phrase in combined_text
        for phrase in [
            "book a consultation",
            "schedule",
            "take the migraine quiz",
            "you do not need to figure this out alone",
            "if you have been delaying care",
        ]
    )
    has_brand_like_marketing_tone = any(
        phrase in combined_text
        for phrase in ["migraine quiz", "booking page", "contact page", "local specialist", "evergreen park"]
    )

    if blog_word_count >= 500:
        strengths.append("The blog asset is a full draft instead of a brief or outline.")
    else:
        improvements.append("Expand the blog asset into a full 500-800 word draft.")

    if landing_specific:
        strengths.append("The landing page refresh outline is specific enough for a marketer or writer to use immediately.")
    else:
        improvements.append("Add more concrete landing page changes tied to the selected page and keyword.")

    if len(faq_block.get("questions", [])) >= 3 and not has_placeholders:
        strengths.append("The FAQ block uses written answers instead of placeholder guidance.")
    else:
        improvements.append("Replace any remaining placeholder-style FAQ answers with fully written copy.")

    if len(social_text.split()) >= 40:
        strengths.append("The social post includes a clear hook, benefit, and CTA.")
    else:
        improvements.append("Make the social post more specific and complete.")

    if has_local_language:
        strengths.append("The content uses local Evergreen Park and Chicago suburbs language naturally.")
    else:
        improvements.append("Add stronger local SEO language such as Evergreen Park and Chicago suburbs.")

    if has_conversion_language:
        strengths.append("The content includes stronger conversion language, reassurance, and urgency.")
    else:
        improvements.append("Add more appointment-driven urgency, reassurance, and CTA language.")

    if fully_written and landing_specific and not has_placeholders and has_local_language and has_conversion_language and has_brand_like_marketing_tone:
        score = 5
    elif blog_word_count >= 450 and landing_specific and not has_placeholders:
        score = 4
        improvements.append("The assets are mostly usable, but they still need a final editorial pass.")
    else:
        score = 3
        improvements.append("The assets are structured, but they still need substantive refinement before use.")

    print(f"[Evaluation Agent] Final score: {score}/5")
    print(f"[Evaluation Agent] Placeholder text detected: {has_placeholders}")

    return {
        "agent": "evaluation",
        "input_agent": execution["agent"],
        "evaluation": {
            "score": score,
            "strengths": strengths,
            "improvements": improvements,
        },
        "notes": [
            "A score of 5 is reserved for fully written assets that feel local, conversion-focused, and brand-specific.",
        ],
    }
