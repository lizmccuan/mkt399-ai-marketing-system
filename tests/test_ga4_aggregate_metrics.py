import unittest

from agents.data_intake import run_data_intake
from utils.parser import parse_csv_text


class GA4AggregateMetricsTest(unittest.TestCase):
    def parse_pages(self, body: str):
        return parse_csv_text(body, "GA4_PAGES")

    def test_grand_total_extraction_removes_summary_row(self):
        dataframe = self.parse_pages(
            "\n".join(
                [
                    "# Example",
                    "Page title,New users,Engagement rate,Active users,Returning users,Sessions,Total users,Average engagement time per session",
                    ",100,0.75,90,20,120,95,33,Grand total",
                    "Page A,60,0.10,50,10,80,55,10",
                    "Page B,40,0.90,45,10,70,45,90",
                ]
            )
        )

        aggregate = dataframe.attrs.get("ga4_aggregate_metrics", {})
        self.assertEqual(aggregate.get("sessions"), 120)
        self.assertEqual(aggregate.get("active_users"), 90)
        self.assertEqual(aggregate.get("total_users"), 95)
        self.assertEqual(aggregate.get("new_users"), 100)
        self.assertEqual(aggregate.get("returning_users"), 20)
        self.assertEqual(aggregate.get("engagement_rate"), 0.75)
        self.assertEqual(aggregate.get("average_engagement_time_per_session"), 33)
        self.assertEqual(dataframe["page_title"].tolist(), ["Page A", "Page B"])

    def test_engagement_rate_uses_grand_total_not_page_mean(self):
        dataframe = self.parse_pages(
            "\n".join(
                [
                    "Page title,New users,Engagement rate,Active users,Returning users,Sessions,Total users,Average engagement time per session",
                    ",100,0.75,90,20,120,95,33,Grand total",
                    "Page A,60,0.10,50,10,80,55,10",
                    "Page B,40,0.90,45,10,70,45,90",
                ]
            )
        )
        intake = run_data_intake(ga4_pages_data=dataframe)
        aggregate = intake["summary"]["ga4_aggregate_metrics"]

        self.assertEqual(aggregate["engagement_rate"], 0.75)
        self.assertNotEqual(aggregate["engagement_rate"], dataframe["engagement_rate"].mean())

    def test_sessions_and_active_users_use_grand_total_not_page_sum(self):
        dataframe = self.parse_pages(
            "\n".join(
                [
                    "Page title,New users,Engagement rate,Active users,Returning users,Sessions,Total users,Average engagement time per session",
                    ",100,0.75,90,20,120,95,33,Grand total",
                    "Page A,60,0.10,50,10,80,55,10",
                    "Page B,40,0.90,45,10,70,45,90",
                ]
            )
        )
        aggregate = run_data_intake(ga4_pages_data=dataframe)["summary"]["ga4_aggregate_metrics"]

        self.assertEqual(aggregate["sessions"], 120)
        self.assertEqual(aggregate["active_users"], 90)
        self.assertNotEqual(aggregate["sessions"], dataframe["sessions"].sum())
        self.assertNotEqual(aggregate["active_users"], dataframe["active_users"].sum())

    def test_missing_aggregate_does_not_fallback_to_page_rows(self):
        dataframe = self.parse_pages(
            "\n".join(
                [
                    "Page title,New users,Engagement rate,Active users,Returning users,Sessions,Total users,Average engagement time per session",
                    "Page A,60,0.10,50,10,80,55,10",
                    "Page B,40,0.90,40,10,70,45,90",
                ]
            )
        )
        aggregate = run_data_intake(ga4_pages_data=dataframe)["summary"]["ga4_aggregate_metrics"]

        self.assertIsNone(aggregate["sessions"])
        self.assertIsNone(aggregate["active_users"])
        self.assertIsNone(aggregate["engagement_rate"])
        self.assertEqual(dataframe["page_title"].tolist(), ["Page A", "Page B"])

    def test_rate_format_is_stored_once_as_source_numeric_value(self):
        dataframe = self.parse_pages(
            "\n".join(
                [
                    "Page title,New users,Engagement rate,Active users,Returning users,Sessions,Total users,Average engagement time per session",
                    ",100,73.86%,90,20,120,95,33,Grand total",
                    "Page A,60,10%,50,10,80,55,10",
                ]
            )
        )
        aggregate = run_data_intake(ga4_pages_data=dataframe)["summary"]["ga4_aggregate_metrics"]

        self.assertEqual(aggregate["engagement_rate"], 73.86)


if __name__ == "__main__":
    unittest.main()
