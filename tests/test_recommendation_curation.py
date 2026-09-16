"""Recommendation curation contract tests."""

import sys
import types
import unittest

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None
    pandas_stub = types.ModuleType("pandas")
    pandas_stub.to_numeric = lambda value, errors="coerce": value
    sys.modules["pandas"] = pandas_stub

from services.recommendation_curation import (
    action_family_for_item,
    build_intent_level_recommendation_items,
    cluster_recommendation_items,
    curate_recommendation_queue,
    has_true_keyword_gap_evidence,
    is_quality_eligible,
    search_intent_key_for_query,
)
from services.rule_engine import _build_ga4_page_payloads, _build_social_payloads
from services.scoring import calculate_rule_scores


def make_item(
    title,
    *,
    rule_id="rule",
    subject="headache oak lawn",
    recommendation="Improve the search result copy.",
    source="Google Search Console",
    source_type="gsc_queries",
    category="SEO",
    priority="High",
    evidence=None,
    sample_data=None,
):
    evidence = evidence or {"impressions": 11038, "clicks": 0, "ctr": 0.0, "position": 4.0}
    return {
        "recommendation_id": f"{rule_id}_{subject}_{title}",
        "rule_id": rule_id,
        "subject": subject,
        "source": source,
        "source_type": source_type,
        "category": category,
        "tab": category,
        "title": title,
        "issue": title,
        "recommendation": recommendation,
        "why_it_matters": "The current evidence supports action.",
        "priority": priority,
        "evidence": evidence,
        "sample_data": sample_data or evidence,
        "confidence_score": 56,
        "business_impact_score": 64,
        "opportunity_score": 80,
    }


class RecommendationCurationTests(unittest.TestCase):
    def test_same_subject_same_evidence_collapses_overlapping_seo_rules(self):
        items = [
            make_item("Strong ranking but low CTR", rule_id="high_position_low_ctr"),
            make_item("High impressions but low CTR", rule_id="high_impressions_low_ctr"),
            make_item("Non-branded search opportunity", rule_id="non_branded_search_opportunity"),
            make_item("Keyword-gap opportunity", rule_id="keyword_gap_opportunity"),
            make_item("Topic-opportunity expansion", rule_id="topic_opportunity_expansion"),
            make_item("Needs FAQ and schema support", rule_id="needs_faq_schema_support"),
        ]

        curated = curate_recommendation_queue(items)

        self.assertLessEqual(len(curated), 3)
        self.assertEqual(curated[0]["_action_family"], "SEO_SEARCH_PERFORMANCE")
        self.assertGreaterEqual(len(curated[0]["_related_items"]), 1)

    def test_strong_ctr_signal_remains_high_priority(self):
        curated = curate_recommendation_queue(
            [make_item("Strong ranking but low CTR", rule_id="high_position_low_ctr")]
        )

        self.assertEqual(curated[0]["priority"], "High")
        self.assertEqual(curated[0]["_evidence_tier"], "strong")

    def test_small_sample_cannot_stay_high_priority_from_query_only(self):
        items = [
            make_item(
                "Strong ranking but low CTR",
                rule_id="high_position_low_ctr",
                subject="tiny query",
                evidence={"impressions": 5, "clicks": 0, "ctr": 0.0, "position": 3.0},
            )
        ]
        clustered = cluster_recommendation_items(items)
        curated = curate_recommendation_queue(items)

        self.assertEqual(clustered[0]["priority"], "Medium")
        self.assertEqual(clustered[0]["_evidence_tier"], "very_small")
        self.assertEqual(curated, [])

    def test_gsc_only_keyword_gap_is_not_labeled_keyword_gap(self):
        item = make_item(
            "Keyword-gap opportunity",
            rule_id="keyword_gap_opportunity",
            recommendation="Close the keyword gap with missing coverage.",
        )

        clustered = cluster_recommendation_items([item])
        curated = curate_recommendation_queue([item])

        self.assertFalse(has_true_keyword_gap_evidence(item))
        self.assertNotIn("keyword gap", clustered[0]["title"].lower())
        self.assertNotIn("missing coverage", clustered[0]["recommendation"].lower())
        self.assertEqual(curated, [])

    def test_legitimate_gap_evidence_can_keep_keyword_gap_family(self):
        item = make_item(
            "Keyword-gap opportunity",
            rule_id="keyword_gap_opportunity",
            source="SEMrush",
            source_type="semrush_positions",
            evidence={"impressions": 500, "position": 18, "keyword_gap_count": 4},
            sample_data={"impressions": 500, "position": 18, "keyword_gap_count": 4},
        )

        self.assertTrue(has_true_keyword_gap_evidence(item))
        self.assertEqual(action_family_for_item(item), "SEO_TRUE_KEYWORD_GAP")

    def test_conversion_language_is_guarded_without_conversion_metrics(self):
        item = make_item(
            "Improve conversion rate",
            rule_id="ux_conversion",
            category="UX/CRO",
            source="Google Analytics 4",
            source_type="ga4_pages",
            recommendation="Improve conversion rate and drive leads from this page.",
            evidence={"sessions": 450, "engagement_rate": 64},
        )

        curated = curate_recommendation_queue([item])
        text = f"{curated[0]['title']} {curated[0]['recommendation']}".lower()

        self.assertNotIn("conversion rate", text)
        self.assertNotIn("drive leads", text)

    def test_one_social_post_uses_cautious_language(self):
        item = make_item(
            "Scale winning social format",
            rule_id="scale_social_format",
            subject="post one",
            category="Social",
            source="Meta",
            source_type="social",
            recommendation="Scale this proven content type.",
            evidence={"reach": 1500, "saves": 12, "follows": 2},
        )

        clustered = cluster_recommendation_items([item])
        curated = curate_recommendation_queue([item])
        text = f"{clustered[0]['title']} {clustered[0]['recommendation']}".lower()

        self.assertIn("promising", text)
        self.assertNotIn("proven", text)
        self.assertEqual(curated, [])

    def test_distinct_actions_for_same_subject_can_remain_separate(self):
        ctr_item = make_item(
            "Strong ranking but low CTR",
            rule_id="high_position_low_ctr",
            recommendation="Improve the title tag and meta description.",
        )
        gap_item = make_item(
            "Keyword-gap opportunity",
            rule_id="keyword_gap_opportunity",
            recommendation="Create supporting content for confirmed missing coverage.",
            source="SEMrush",
            source_type="semrush_positions",
            evidence={"impressions": 500, "position": 18, "keyword_gap_count": 4},
            sample_data={"impressions": 500, "position": 18, "keyword_gap_count": 4},
        )

        curated = curate_recommendation_queue([ctr_item, gap_item])

        self.assertEqual(len(curated), 2)
        self.assertEqual({item["_action_family"] for item in curated}, {"SEO_SEARCH_PERFORMANCE", "SEO_TRUE_KEYWORD_GAP"})

    def test_missing_ga4_conversions_remain_missing(self):
        data = {
            "summary": {
                "ga4_pages": {
                    "sample_records": [
                        {
                            "page_title": "Service Page",
                            "sessions": 100,
                            "active_users": 90,
                            "engagement_rate": 62,
                        }
                    ]
                }
            }
        }

        _, payload = _build_ga4_page_payloads(data)[0]

        self.assertIsNone(payload["conversions"])

    def test_ga4_zero_conversions_remain_genuine_zero(self):
        data = {
            "summary": {
                "ga4_pages": {
                    "sample_records": [
                        {
                            "page_title": "Service Page",
                            "sessions": 100,
                            "active_users": 90,
                            "engagement_rate": 0.2,
                            "conversions": 0,
                        }
                    ]
                }
            }
        }

        _, payload = _build_ga4_page_payloads(data)[0]

        self.assertEqual(payload["conversions"], 0.0)

    def test_social_follows_are_not_recast_as_conversions(self):
        if pd is None:
            self.skipTest("pandas is not installed in this runtime")
        posts = pd.DataFrame(
            [
                {
                    "Hook": "Strong post",
                    "Reach": 1200,
                    "Engagement Rate": 1.5,
                    "Follows": 4,
                    "Saves": 8,
                }
            ]
        )

        _, payload = _build_social_payloads(posts)[0]

        self.assertEqual(payload["follows"], 4)
        self.assertEqual(payload["saves"], 8)
        self.assertNotIn("conversions", payload)

    def test_botox_savings_intent_variants_consolidate(self):
        items = [
            make_item("Strong ranking but low CTR", subject="botox savings", rule_id="ctr_1"),
            make_item("Strong ranking but low CTR", subject="botox savings program", rule_id="ctr_2"),
            make_item("Strong ranking but low CTR", subject="botoxsavingsprogram", rule_id="ctr_3"),
            make_item("Strong ranking but low CTR", subject="abbvie botox savings program", rule_id="ctr_4"),
        ]

        curated = curate_recommendation_queue(items)

        self.assertEqual(len(curated), 1)
        self.assertEqual(curated[0]["_search_intent"], "Botox Savings Program")
        self.assertEqual(curated[0]["_intent_cluster_size"], 4)

    def test_distinct_botox_topics_do_not_merge(self):
        curated = curate_recommendation_queue(
            [
                make_item("Strong ranking but low CTR", subject="botox savings", rule_id="ctr_1"),
                make_item("Strong ranking but low CTR", subject="botox for blepharospasm", rule_id="ctr_2"),
            ]
        )

        self.assertEqual(len(curated), 2)
        self.assertEqual(
            {item["_search_intent"] for item in curated},
            {"Botox Savings Program", "Botox Blepharospasm"},
        )

    def test_migraine_quiz_ctr_and_ranking_consolidate(self):
        ctr_item = make_item(
            "Strong ranking but low CTR",
            subject="migraine quiz",
            rule_id="high_position_low_ctr",
            recommendation="Improve title and snippet click appeal.",
        )
        ranking_item = make_item(
            "AI citation authority opportunity",
            subject="migraine quiz",
            rule_id="ai_citation_authority_opportunity",
            recommendation="Add authority signals to improve ranking growth.",
        )

        intent_items = build_intent_level_recommendation_items([ctr_item, ranking_item])

        self.assertEqual(len(intent_items), 1)
        self.assertEqual(intent_items[0]["_action_family"], "SEO_SEARCH_PERFORMANCE")

    def test_gsc_query_without_landing_page_does_not_claim_specific_page(self):
        curated = curate_recommendation_queue(
            [make_item("Strong ranking but low CTR", subject="botox savings")]
        )

        text = f"{curated[0]['title']} {curated[0]['recommendation']}".lower()

        self.assertNotIn("optimize the page", text)
        self.assertIn("without assuming a specific landing page", text)

    def test_weak_social_does_not_enter_queue_for_category_balance(self):
        weak_social = make_item(
            "Scale winning social format",
            rule_id="social",
            subject="post one",
            category="Social",
            source="Meta",
            source_type="social",
            evidence={"reach": 500},
            recommendation="Test this promising post format.",
        )
        strong_seo = make_item("Strong ranking but low CTR", subject="headache oak lawn")

        curated = curate_recommendation_queue([strong_seo, weak_social])

        self.assertEqual(len(curated), 1)
        self.assertEqual(curated[0]["_search_intent"], "Headache Oak Lawn")

    def test_unsupported_authority_does_not_become_standalone_item(self):
        item = make_item(
            "AI citation authority opportunity",
            rule_id="ai_citation_authority_opportunity",
            recommendation="Add citations and authority signals to improve AI citation potential.",
        )

        self.assertFalse(is_quality_eligible(cluster_recommendation_items([item])[0]))
        self.assertEqual(curate_recommendation_queue([item]), [])

    def test_ga4_source_is_not_page_refresh_recommendation(self):
        item = make_item(
            "Weak page refresh opportunity",
            rule_id="weak_page_refresh_opportunity",
            subject="ig / paid",
            source="Google Analytics 4",
            source_type="ga4_sources",
            category="UX/CRO",
            evidence={"sessions": 222, "active_users": 223, "engagement_rate": 0.02},
            recommendation="Refresh the headline, intro, page structure, CTA flow, and supporting proof.",
        )

        curated = curate_recommendation_queue([item])

        self.assertEqual(curated[0]["_action_family"], "ANALYTICS")
        self.assertIn("Review engagement quality from ig / paid traffic", curated[0]["title"])
        self.assertNotIn("page refresh", curated[0]["title"].lower())
        self.assertNotIn("the page may not match", curated[0]["why_it_matters"].lower())

    def test_ga4_page_recommendation_names_known_page_asset(self):
        item = make_item(
            "Weak page refresh opportunity",
            rule_id="weak_page_refresh_opportunity",
            subject="Migraine & Headache Treatment Westmont, IL | The Headache Lab",
            source="Google Analytics 4",
            source_type="ga4_pages",
            category="UX/CRO",
            evidence={"sessions": 289, "active_users": 285, "engagement_rate": 0.055},
            recommendation="Refresh the headline, intro, page structure, CTA flow, and supporting proof.",
        )

        curated = curate_recommendation_queue([item])

        self.assertEqual(curated[0]["_action_family"], "UX_CRO")
        self.assertEqual(
            curated[0]["title"],
            "Review the Migraine & Headache Treatment Westmont, IL page experience",
        )
        self.assertNotEqual(curated[0]["title"], "Weak page refresh opportunity")

    def test_ga4_source_explanation_stays_acquisition_level(self):
        item = make_item(
            "Weak page refresh opportunity",
            rule_id="weak_page_refresh_opportunity",
            subject="ig / paid",
            source="Google Analytics 4",
            source_type="ga4_sources",
            category="UX/CRO",
            evidence={"sessions": 222, "active_users": 223, "engagement_rate": 0.02},
            recommendation="Refresh the headline, intro, page structure, CTA flow, and supporting proof.",
        )

        curated = curate_recommendation_queue([item])
        explanation = " ".join(
            [
                curated[0].get("recommendation", ""),
                curated[0].get("why_it_matters", ""),
            ]
        ).lower()

        self.assertIn("acquisition path", explanation)
        self.assertIn("ig / paid traffic", curated[0]["title"])
        self.assertNotIn("the page may not match", explanation)
        self.assertNotIn("weak page", explanation)

    def test_queue_size_is_not_padded_to_maximum(self):
        items = [
            make_item("Strong ranking but low CTR", subject=f"topic {index}", evidence={"impressions": 80 + index, "clicks": 0, "ctr": 0, "position": 5})
            for index in range(9)
        ]

        curated = curate_recommendation_queue(items, max_items=20)

        self.assertEqual(len(curated), 9)

    def test_cluster_size_does_not_inflate_priority(self):
        items = [
            make_item("Strong ranking but low CTR", subject="tiny query", rule_id=f"rule_{index}", evidence={"impressions": 5, "clicks": 0, "ctr": 0, "position": 3})
            for index in range(6)
        ]

        intent_items = build_intent_level_recommendation_items(items)

        self.assertEqual(intent_items[0]["priority"], "Medium")
        self.assertEqual(intent_items[0]["_intent_cluster_size"], 1)

    def test_headache_clinic_intent_normalization_is_conservative(self):
        self.assertEqual(search_intent_key_for_query("headache clinic"), "headache clinic")
        self.assertEqual(search_intent_key_for_query("headache clinic chicago"), "headache clinic")
        self.assertEqual(search_intent_key_for_query("is chicago headache clinic legit"), "headache clinic trust")
        self.assertEqual(search_intent_key_for_query("headache labs"), "headache labs")

    def test_strong_direct_gsc_confidence_exceeds_small_direct_gsc_confidence(self):
        strong = make_item(
            "Strong ranking but low CTR",
            subject="strong query",
            evidence={"impressions": 11038, "clicks": 0, "ctr": 0.0, "position": 4.0},
        )
        small = make_item(
            "Strong ranking but low CTR",
            subject="small query",
            evidence={"impressions": 55, "clicks": 0, "ctr": 0.0, "position": 1.0},
        )

        curated = {item["_search_intent"]: item for item in curate_recommendation_queue([strong, small])}

        self.assertGreater(curated["Strong Query"]["confidence_score"], curated["Small Query"]["confidence_score"])

    def test_rule_condition_count_alone_does_not_raise_display_confidence(self):
        one_condition = make_item(
            "Strong ranking but low CTR",
            subject="condition one",
            evidence={"impressions": 300, "clicks": 0, "ctr": 0.0, "position": 8.0},
        )
        three_conditions = make_item(
            "Strong ranking but low CTR",
            subject="condition three",
            evidence={"impressions": 300, "clicks": 0, "ctr": 0.0, "position": 8.0},
        )
        one_condition["confidence_score"] = 40
        three_conditions["confidence_score"] = 95

        curated = {item["_search_intent"]: item for item in curate_recommendation_queue([one_condition, three_conditions])}

        self.assertEqual(curated["Condition One"]["confidence_score"], curated["Condition Three"]["confidence_score"])

    def test_consolidated_intent_confidence_uses_supporting_evidence(self):
        low_raw_confidence = make_item(
            "Strong ranking but low CTR",
            subject="botox savings",
            rule_id="ctr_1",
            evidence={"impressions": 285, "clicks": 0, "ctr": 0.0, "position": 7.97},
        )
        variant = make_item(
            "Strong ranking but low CTR",
            subject="botox savings program",
            rule_id="ctr_2",
            evidence={"impressions": 338, "clicks": 0, "ctr": 0.0, "position": 9.55},
        )
        low_raw_confidence["confidence_score"] = 10
        variant["confidence_score"] = 10

        curated = curate_recommendation_queue([low_raw_confidence, variant])

        self.assertEqual(curated[0]["_search_intent"], "Botox Savings Program")
        self.assertEqual(curated[0]["confidence_score"], 85.0)
        self.assertEqual(curated[0]["_raw_confidence_score"], 10)

    def test_duplicate_supporting_query_records_do_not_inflate_confidence(self):
        duplicates = [
            make_item(
                "Strong ranking but low CTR",
                subject="botox savings",
                rule_id=f"duplicate_{index}",
                evidence={"impressions": 600, "clicks": 0, "ctr": 0.0, "position": 8.0},
            )
            for index in range(3)
        ]

        curated = curate_recommendation_queue(duplicates)

        self.assertEqual(curated[0]["_intent_cluster_size"], 1)
        self.assertEqual(curated[0]["confidence_score"], 85.0)

    def test_missing_conversions_do_not_reduce_non_conversion_confidence(self):
        missing_conversion = make_item(
            "Weak page refresh opportunity",
            subject="Known Service Page",
            source="Google Analytics 4",
            source_type="ga4_pages",
            category="UX/CRO",
            evidence={"sessions": 289, "active_users": 285, "engagement_rate": 0.055},
            recommendation="Review the page experience and next-step clarity.",
        )
        zero_conversion = make_item(
            "Weak page refresh opportunity",
            subject="Known Service Page With Zero",
            source="Google Analytics 4",
            source_type="ga4_pages",
            category="UX/CRO",
            evidence={"sessions": 289, "active_users": 285, "engagement_rate": 0.055, "conversions": 0},
            recommendation="Review the page experience and next-step clarity.",
        )

        curated = {item["subject"]: item for item in curate_recommendation_queue([missing_conversion, zero_conversion])}

        self.assertEqual(curated["Known Service Page"]["confidence_score"], curated["Known Service Page With Zero"]["confidence_score"])

    def test_direct_evidence_scores_higher_than_inferred_claim(self):
        direct = make_item(
            "Weak page refresh opportunity",
            subject="Direct Page",
            source="Google Analytics 4",
            source_type="ga4_pages",
            category="UX/CRO",
            evidence={"sessions": 289, "active_users": 285, "engagement_rate": 0.055},
            recommendation="Review the page experience and next-step clarity.",
        )
        inferred = make_item(
            "Weak page refresh opportunity",
            subject="Inferred Page",
            source="Google Analytics 4",
            source_type="ga4_pages",
            category="UX/CRO",
            evidence={"sessions": 289, "active_users": 285, "engagement_rate": 0.055},
            recommendation="This may indicate a broader visitor intent mismatch.",
        )

        curated = {item["subject"]: item for item in curate_recommendation_queue([direct, inferred])}

        self.assertGreater(curated["Direct Page"]["confidence_score"], curated["Inferred Page"]["confidence_score"])

    def test_scoring_distinguishes_missing_conversions_from_zero_conversions(self):
        rule = {"action_type": "ux_cro", "conditions": {"all": []}}
        base_sample = {"sessions": 250, "active_users": 240, "engagement_rate": 0.05}
        missing_conversion_scores = calculate_rule_scores(rule, base_sample)
        zero_conversion_scores = calculate_rule_scores(rule, {**base_sample, "conversions": 0})

        self.assertLess(
            missing_conversion_scores["business_impact_score"],
            zero_conversion_scores["business_impact_score"],
        )
        self.assertLess(
            missing_conversion_scores["opportunity_score"],
            zero_conversion_scores["opportunity_score"],
        )

    def test_missing_conversions_add_no_conversion_opportunity_score(self):
        rule = {"action_type": "ux_cro", "conditions": {"all": []}}
        scores = calculate_rule_scores(
            rule,
            {"sessions": 250, "active_users": 240, "engagement_rate": 0.05},
        )

        self.assertAlmostEqual(scores["business_impact_score"], 40.58, places=2)
        self.assertAlmostEqual(scores["opportunity_score"], 31.22, places=2)

    def test_actual_zero_conversions_can_still_score_conversion_opportunity(self):
        rule = {"action_type": "ux_cro", "conditions": {"all": []}}
        scores = calculate_rule_scores(
            rule,
            {"sessions": 250, "active_users": 240, "engagement_rate": 0.05, "conversions": 0},
        )

        self.assertAlmostEqual(scores["business_impact_score"], 62.58, places=2)
        self.assertAlmostEqual(scores["opportunity_score"], 41.22, places=2)

    def test_westmont_style_ga4_without_conversions_has_no_artificial_conversion_upside(self):
        rule = {"action_type": "ux_cro", "conditions": {"all": []}}
        scores = calculate_rule_scores(
            rule,
            {"sessions": 289, "active_users": 285, "engagement_rate": 0.05536332179930796},
        )

        self.assertAlmostEqual(scores["business_impact_score"], 40.48, places=2)
        self.assertAlmostEqual(scores["opportunity_score"], 31.11, places=2)


if __name__ == "__main__":
    unittest.main()
