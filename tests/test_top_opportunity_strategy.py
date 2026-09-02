"""Focused contract tests for evidence-grounded search opportunity explanations."""

import sys
import types
import unittest

# These focused tests do not exercise dataframe behavior. This lightweight
# fallback lets the pure strategy contract be tested in a syntax-only runtime.
try:
    import pandas  # noqa: F401
except ModuleNotFoundError:
    sys.modules["pandas"] = types.ModuleType("pandas")

from agents.insight_agent import analyze_queries, run_insight_agent
from agents.strategy_agent import build_top_opportunity_conclusion, run_strategy_agent
from services.rule_engine import _build_gsc_query_payloads, evaluate_decision_rules
from services.scoring import normalize_rule_ctr_value
from utils.parser import normalize_gsc_ctr_percent


class TopOpportunityStrategyTests(unittest.TestCase):
    def build_conclusion(self, **record):
        query = analyze_queries([{"query": "example topic", **record}])[0]
        return build_top_opportunity_conclusion(query)

    def test_high_impressions_low_ctr_uses_search_result_messaging(self):
        conclusion = self.build_conclusion(impressions=10_000, clicks=150, position=4)

        self.assertEqual(conclusion["diagnosis"], "Search-result click-through opportunity")
        self.assertIn("title tag", conclusion["recommended_next_step"])

    def test_strong_ctr_mid_ranking_uses_ranking_growth(self):
        conclusion = self.build_conclusion(impressions=500, clicks=400, position=10)

        self.assertEqual(conclusion["diagnosis"], "Ranking growth opportunity")
        self.assertIn("higher Google position", conclusion["recommended_next_step"])
        self.assertNotIn("meta description", conclusion["recommended_next_step"])

    def test_top_ranking_with_strong_ctr_is_not_labeled_as_an_issue(self):
        conclusion = self.build_conclusion(impressions=2_000, clicks=800, position=2)

        self.assertEqual(conclusion["diagnosis"], "Strong search performer")
        self.assertIn("Protect", conclusion["recommended_next_step"])

    def test_missing_ctr_does_not_create_a_ctr_claim(self):
        conclusion = self.build_conclusion(impressions=1_000, position=9)

        self.assertNotIn("ctr", conclusion["evidence"])
        self.assertNotIn("click-through", conclusion["business_summary"].lower())

    def test_strategy_runs_for_search_data_without_semrush_or_meta(self):
        query = analyze_queries([{"query": "example topic", "impressions": 236, "clicks": 201, "position": 10}])[0]
        insights = {
            "agent": "insight",
            "insights": [],
            "patterns": [],
            "high_impression_low_click": [],
            "conversion_intent_queries": [],
            "non_branded_queries": [query],
            "local_intent_queries": [],
            "aligned_pages": [],
            "top_pages": [],
        }

        strategy = run_strategy_agent(insights)

        self.assertEqual(strategy["strategy"]["top_opportunity"]["diagnosis"], "Ranking growth opportunity")

    def test_strong_ctr_does_not_match_a_low_ctr_rule(self):
        low_ctr_rule = {
            "id": "high_impressions_low_ctr",
            "conditions": {
                "all": [
                    {"field": "impressions", "operator": ">=", "value": 1000},
                    {"field": "ctr", "operator": "<=", "value": 5.0},
                ]
            },
        }

        triggered, _ = evaluate_decision_rules([low_ctr_rule], {"impressions": 1500, "ctr": 85})

        self.assertEqual(triggered, [])

    def test_ctr_below_one_percent_remains_percentage_points(self):
        query = analyze_queries(
            [{"query": "low ctr topic", "impressions": 1_000, "clicks": 8, "position": 7}]
        )[0]

        self.assertEqual(query["ctr"], 0.8)
        self.assertEqual(normalize_rule_ctr_value(query["ctr"]), 0.008)

    def test_aggregate_non_branded_ctr_matches_five_percent_threshold(self):
        insights = {
            "full_query_analysis": [
                analyze_queries(
                    [{"query": "non branded topic", "impressions": 1_000, "clicks": 30, "position": 8}]
                )[0]
            ]
        }
        insights["non_branded_queries"] = insights["full_query_analysis"]
        _, aggregate_payload = _build_gsc_query_payloads({}, insights)[-1]
        rule = {
            "id": "non_branded_ctr_opportunity",
            "conditions": {
                "all": [
                    {"field": "non_branded_impressions", "operator": ">=", "value": 500},
                    {"field": "non_branded_ctr", "operator": "<=", "value": 5.0},
                ]
            },
        }

        triggered, _ = evaluate_decision_rules([rule], aggregate_payload)

        self.assertEqual(aggregate_payload["non_branded_ctr"], 3.0)
        self.assertEqual([rule["id"] for rule in triggered], [rule["id"]])

    def test_meta_engagement_rate_uses_percentage_point_threshold(self):
        rule = {
            "id": "low_social_engagement",
            "action_type": "social",
            "conditions": {
                "all": [
                    {"field": "reach", "operator": ">=", "value": 1_000},
                    {"field": "engagement_rate", "operator": "<=", "value": 2.0},
                ]
            },
        }

        triggered, _ = evaluate_decision_rules([rule], {"reach": 1_000, "engagement_rate": 1.5})

        self.assertEqual([rule["id"] for rule in triggered], [rule["id"]])

    def test_evidence_preserves_raw_gsc_click_count(self):
        query = analyze_queries(
            [{"query": "click evidence", "impressions": 236, "clicks": 201, "ctr": 85, "position": 10}]
        )[0]

        self.assertEqual(query["evidence"]["clicks"], 201.0)
        self.assertNotEqual(query["evidence"]["clicks"], 200.6)

    def test_missing_raw_clicks_are_not_reconstructed_from_ctr(self):
        query = analyze_queries(
            [{"query": "no raw clicks", "impressions": 236, "ctr": 85, "position": 10}]
        )[0]

        self.assertNotIn("clicks", query["evidence"])
        self.assertEqual(build_top_opportunity_conclusion(query)["diagnosis"], "Ranking growth opportunity")

    def test_missing_impressions_produces_limited_evidence(self):
        conclusion = self.build_conclusion(ctr=4, position=7)

        self.assertEqual(conclusion["diagnosis"], "Limited search evidence")
        self.assertNotIn("high", conclusion["business_summary"].lower())
        self.assertIsNone(normalize_gsc_ctr_percent(None, clicks=None, impressions=None))

    def test_actionable_query_beats_strong_performer_for_top_opportunity(self):
        strong_performer = analyze_queries(
            [{"query": "strong performer", "impressions": 2_000, "clicks": 800, "position": 2}]
        )[0]
        actionable = analyze_queries(
            [{"query": "ranking opportunity", "impressions": 500, "clicks": 400, "position": 10}]
        )[0]
        insights = self.strategy_insights([strong_performer, actionable])

        strategy = run_strategy_agent(insights)

        self.assertEqual(strategy["strategy"]["top_opportunity"]["subject"], "ranking opportunity")
        self.assertEqual(strategy["strategy"]["top_opportunity"]["diagnosis"], "Ranking growth opportunity")

    def test_full_gsc_dataset_is_analyzed_beyond_preview_records(self):
        preview_records = [
            {"query": f"preview {index}", "impressions": 2_000, "clicks": 800, "position": 2}
            for index in range(5)
        ]
        full_records = preview_records + [
            {"query": "sixth row opportunity", "impressions": 1_000, "clicks": 10, "position": 9}
        ]
        data = {
            "agent": "data_intake",
            "summary": {
                "ga4_pages": {"rows": 0, "columns": []},
                "ga4_sources": {"rows": 0, "columns": []},
                "gsc_queries": {"rows": len(full_records), "columns": ["query", "clicks", "impressions", "ctr", "position"], "sample_records": preview_records},
                "combined": {"top_pages": [], "top_traffic_sources": []},
            },
            "datasets": {"gsc_queries": full_records},
        }

        insight = run_insight_agent(data)
        strategy = run_strategy_agent(insight)

        self.assertEqual(len(insight["query_analysis"]), 5)
        self.assertEqual(len(insight["full_query_analysis"]), 6)
        self.assertEqual(strategy["strategy"]["top_opportunity"]["subject"], "sixth row opportunity")

    @staticmethod
    def strategy_insights(queries):
        return {
            "agent": "insight",
            "insights": [],
            "patterns": [],
            "query_analysis": queries,
            "full_query_analysis": queries,
            "high_impression_low_click": [query for query in queries if query["is_high_impression_low_click"]],
            "conversion_intent_queries": [],
            "non_branded_queries": queries,
            "local_intent_queries": [],
            "aligned_pages": [],
            "top_pages": [],
        }


if __name__ == "__main__":
    unittest.main()
