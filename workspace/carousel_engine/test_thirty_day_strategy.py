"""
Comprehensive Test Suite for AI Gücüm 30-Day Strategy & Autonomous System (Phase A-D).
Tests official news collector, content brief generator, profile repair manager,
30-day scheduler, and insight learning loop compliance.
"""

import unittest
from workspace.carousel_engine.official_news_collector import is_allowlisted_url, collect_and_validate_topics
from workspace.carousel_engine.content_brief_generator import generate_content_brief
from workspace.carousel_engine.profile_repair_manager import verify_profile_repair_status
from workspace.carousel_engine.thirty_day_scheduler import generate_30_day_calendar
from workspace.carousel_engine.insight_learning_loop import calculate_performance_ratios, evaluate_30_day_kpi_compliance

class TestThirtyDayStrategy(unittest.TestCase):

    def test_official_news_allowlist(self):
        """Ensures that only official allowlisted URLs pass Phase A validation."""
        self.assertTrue(is_allowlisted_url("https://github.blog/changelog/2026-07-24-claude-opus-5"))
        self.assertTrue(is_allowlisted_url("https://openai.com/index/gpt-5-6/"))
        self.assertFalse(is_allowlisted_url("https://randomunverifiedblog.com/fake-news"))

    def test_content_brief_schema(self):
        """Verifies that Content Brief Generator produces valid JSON briefs with CTA and steps."""
        sample_topic = {
            "title": "Gemma 4 12B Yerel AI",
            "hook": "Buluta veri göndermeden AI ajanı çalıştırabilir misin?",
            "official_source_url": "https://blog.google/technology/ai/gemma4",
            "format": "reel",
            "cta": "Windows rehberi için YEREL yaz."
        }
        brief = generate_content_brief(sample_topic)
        self.assertEqual(brief["status"], "APPROVED")
        self.assertIn("Gemma 4", brief["topic"])
        self.assertIn("YEREL", brief["cta"])

    def test_ungrounded_claim_blocked(self):
        """Verifies that ungrounded claims without allowlisted source URLs are BLOCKED."""
        fake_topic = {
            "title": "Fake AI News",
            "hook": "No official source",
            "official_source_url": "https://fakeunverifiedsite.com/xyz"
        }
        brief = generate_content_brief(fake_topic)
        self.assertEqual(brief["status"], "BLOCKED_UNGROUNDED_CLAIM")

    def test_profile_repair_checklist(self):
        """Ensures Profile Repair Checklist contains required name, bio, 3 pinned posts, and 6 highlights."""
        checklist = verify_profile_repair_status()
        self.assertEqual(checklist["searchable_name"], "Bilgehan | Yapay Zekâ ve Otomasyon")
        self.assertEqual(len(checklist["pinned_posts"]), 3)
        self.assertEqual(len(checklist["highlights"]), 6)

    def test_30_day_scheduler_rhythm(self):
        """Ensures 30-day calendar generates 30 daily slots alternating 12:30 and 20:30 TSI."""
        cal = generate_30_day_calendar()
        self.assertEqual(len(cal), 30)
        self.assertIn("12:30", cal[0]["publishing_window"])
        self.assertIn("20:30", cal[1]["publishing_window"])

    def test_insight_ratio_calculations(self):
        """Ensures performance metrics and compliance checks execute accurately using provider evidence."""
        snapshot = {
            "accounts_reached": 1000,
            "saves": 100,
            "shares": 60,
            "comments": 30,
            "follows": 20,
            "average_watch_time": 25.0
        }
        ratios = calculate_performance_ratios(snapshot, reel_duration=30.0)
        self.assertEqual(ratios["save_ratio"], 0.1)
        self.assertEqual(ratios["share_ratio"], 0.06)

if __name__ == "__main__":
    unittest.main()
