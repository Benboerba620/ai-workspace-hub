"""Regression tests for the daily-watch bug-fix batch.

Covers:
- B2: hypothesis_tracking.enabled / auto_writeback are honored (pure logic)
- B3: related-ticker extraction supports CN/HK/dotted/single-letter tickers
- B4: fallback sources only strip known market suffixes (BRK.B stays intact)
- B5: yfinance symbol mapping (.SH -> .SS)
- B8: tolerant certainty parsing + frontmatter YAML error handling
- #9: focus_areas.exclude is enforced
- #12: evidence-timeline entries insert before a trailing horizontal rule
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _test_paths import REPO_ROOT  # noqa: F401 (also sets up sys.path)

from fetch_market_data import strip_market_suffix, to_yfinance_symbol  # noqa: E402
from generate_daily_report import (  # noqa: E402
    append_to_date_block,
    build_hypothesis_section,
    extract_related_tickers,
    hypothesis_settings,
    load_env_file,
    matches_focus_area,
)
from sync_hypothesis import (  # noqa: E402
    extract_frontmatter,
    format_certainty_bar,
    parse_certainty,
    read_hypothesis_files,
)


class HypothesisSettingsTests(unittest.TestCase):
    """B2: enabled / auto_writeback config gating."""

    def test_defaults_are_enabled_and_writeback(self) -> None:
        self.assertEqual(hypothesis_settings({}), (True, True))
        self.assertEqual(hypothesis_settings({"hypothesis_tracking": {}}), (True, True))

    def test_enabled_false_is_respected(self) -> None:
        config = {"hypothesis_tracking": {"enabled": False}}
        self.assertEqual(hypothesis_settings(config), (False, True))

    def test_auto_writeback_false_is_respected(self) -> None:
        config = {"hypothesis_tracking": {"auto_writeback": False}}
        self.assertEqual(hypothesis_settings(config), (True, False))

    def test_non_mapping_config_falls_back_to_defaults(self) -> None:
        self.assertEqual(
            hypothesis_settings({"hypothesis_tracking": "yes"}), (True, True)
        )

    def test_report_section_says_writeback_skipped_when_disabled(self) -> None:
        hypotheses = [
            {
                "id": "H1",
                "title": "测试假设",
                "certainty": 80,
                "status": "观察",
                "tickers": {"NVDA"},
            }
        ]
        signals = [
            {
                "hypothesis_id": "H1",
                "hypothesis_title": "测试假设",
                "signal_type": "mover",
                "ref": "NVDA",
                "display": "- H1 `测试假设` <- NVDA +5.00%",
                "summary": "NVDA +5.00%",
                "auto_writeback": True,
            }
        ]
        disabled = build_hypothesis_section(
            hypotheses, signals, {"hypothesis_tracking": {"auto_writeback": False}}
        )
        self.assertIn("auto_writeback` 已关闭", disabled)
        self.assertNotIn("已将本地可确认信号自动回写", disabled)

        enabled = build_hypothesis_section(
            hypotheses, signals, {"hypothesis_tracking": {"auto_writeback": True}}
        )
        self.assertIn("已将本地可确认信号自动回写", enabled)


class RelatedTickerExtractionTests(unittest.TestCase):
    """B3: ticker patterns in the 关联标的 table."""

    CONTENT = "\n".join(
        [
            "# H1: 测试假设",
            "",
            "## 关联标的",
            "",
            "| 公司 | 角色 | 主题 |",
            "|------|------|------|",
            "| 601857.SH | 核心标的 | 油气 |",
            "| 0700.HK | 核心标的 | 互联网 |",
            "| BRK.B | 对照 | 保险 |",
            "| F | 对照 | 汽车 |",
            "| NVDA | 核心标的 | AI |",
            "| Apple | 公司名不该被当 ticker | 硬件 |",
            "| 中石油 | 中文名不该被当 ticker | 油气 |",
            "| GPU SUPPLY | 普通词组不该被当 ticker | AI |",
            "",
            "## 证据时间线",
        ]
    )

    def test_cn_hk_dotted_and_single_letter_tickers_are_extracted(self) -> None:
        tickers = extract_related_tickers(self.CONTENT)
        self.assertEqual(tickers, {"601857.SH", "0700.HK", "BRK.B", "F", "NVDA"})

    def test_mixed_case_words_are_not_tickers(self) -> None:
        tickers = extract_related_tickers(self.CONTENT)
        self.assertNotIn("APPLE", tickers)
        self.assertNotIn("Apple", tickers)


class SuffixHandlingTests(unittest.TestCase):
    """B4 + B5: fallback symbol normalization."""

    def test_known_market_suffixes_are_stripped(self) -> None:
        self.assertEqual(strip_market_suffix("601857.SH"), "601857")
        self.assertEqual(strip_market_suffix("000001.SZ"), "000001")
        self.assertEqual(strip_market_suffix("0700.HK"), "0700")
        self.assertEqual(strip_market_suffix("005930.KS"), "005930")

    def test_share_class_suffixes_are_preserved(self) -> None:
        # Stripping BF.B -> BF would query a different listed company.
        self.assertEqual(strip_market_suffix("BRK.B"), "BRK.B")
        self.assertEqual(strip_market_suffix("BF.B"), "BF.B")
        self.assertEqual(strip_market_suffix("AAPL"), "AAPL")

    def test_yfinance_maps_shanghai_suffix(self) -> None:
        self.assertEqual(to_yfinance_symbol("601857.SH"), "601857.SS")
        self.assertEqual(to_yfinance_symbol("000001.SZ"), "000001.SZ")
        self.assertEqual(to_yfinance_symbol("0700.HK"), "0700.HK")
        self.assertEqual(to_yfinance_symbol("AAPL"), "AAPL")


class CertaintyParsingTests(unittest.TestCase):
    """B8: tolerant certainty parsing and YAML error handling."""

    def test_parse_certainty_accepts_common_shapes(self) -> None:
        self.assertEqual(parse_certainty(75), 75)
        self.assertEqual(parse_certainty(75.6), 75)
        self.assertEqual(parse_certainty("80"), 80)
        self.assertEqual(parse_certainty("80%"), 80)
        self.assertEqual(parse_certainty(" 80 % "), 80)

    def test_parse_certainty_rejects_junk_without_crashing(self) -> None:
        self.assertIsNone(parse_certainty(None))
        self.assertIsNone(parse_certainty("high"))
        self.assertIsNone(parse_certainty(True))

    def test_format_certainty_bar_uses_tolerant_parsing(self) -> None:
        self.assertEqual(format_certainty_bar("80%"), "🟢 80%")
        self.assertEqual(format_certainty_bar(50), "🟡 50%")
        self.assertEqual(format_certainty_bar(10), "🔴 10%")
        self.assertEqual(format_certainty_bar(None), "—")
        self.assertEqual(format_certainty_bar("junk"), "—")

    def test_invalid_frontmatter_yaml_returns_empty_dict(self) -> None:
        content = "---\nfoo: [1, 2\n---\n\n# H1: 测试\n"
        self.assertEqual(extract_frontmatter(content, source="H1.md"), {})

    def test_one_bad_file_does_not_break_the_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hypothesis_dir = Path(tmp)
            (hypothesis_dir / "H1.md").write_text(
                "---\ncertainty: 80\nstatus: 观察\n---\n\n# H1: 好文件\n",
                encoding="utf-8",
            )
            (hypothesis_dir / "H2.md").write_text(
                "---\ncertainty: [broken\n---\n\n# H2: 坏 frontmatter\n",
                encoding="utf-8",
            )
            data = read_hypothesis_files(hypothesis_dir)
            self.assertEqual(set(data), {"H1", "H2"})
            self.assertEqual(data["H1"]["certainty"], 80)
            self.assertIsNone(data["H2"]["certainty"])


class FocusAreaExcludeTests(unittest.TestCase):
    """#9: focus_areas.exclude is enforced."""

    AREA = {
        "name": "AI 与数据中心",
        "keywords": ["AI", "GPU"],
        "exclude": ["airline"],
    }

    def test_matching_hypothesis_without_excluded_keyword(self) -> None:
        hypothesis = {"title": "AI capex", "content": "GPU demand keeps rising."}
        self.assertTrue(matches_focus_area(hypothesis, self.AREA))

    def test_excluded_keyword_blocks_the_match(self) -> None:
        hypothesis = {
            "title": "AI capex",
            "content": "GPU demand, but mostly about airline routes.",
        }
        self.assertFalse(matches_focus_area(hypothesis, self.AREA))

    def test_required_any_still_applies(self) -> None:
        area = {**self.AREA, "required_any": ["inference"]}
        hypothesis = {"title": "AI capex", "content": "GPU demand keeps rising."}
        self.assertFalse(matches_focus_area(hypothesis, area))


class TimelineInsertionTests(unittest.TestCase):
    """#12: new date blocks insert before a trailing horizontal rule."""

    def test_new_date_block_goes_before_trailing_rule(self) -> None:
        section_body = (
            "\n### 2026-01-01\n\n- 🟡 **[old]** - 旧证据\n\n---\n\n"
        )
        updated = append_to_date_block(section_body, "2026-07-05", "- 🟡 **[new]** - 新证据")
        self.assertIn("### 2026-07-05", updated)
        self.assertLess(
            updated.index("### 2026-07-05"),
            updated.rindex("---"),
            "new date block should sit before the trailing horizontal rule",
        )
        # Existing content preserved.
        self.assertIn("### 2026-01-01", updated)
        self.assertIn("旧证据", updated)

    def test_existing_date_block_is_appended_in_place(self) -> None:
        section_body = "\n### 2026-07-05\n\n- 🟡 **[a]** - 证据一\n\n---\n\n"
        updated = append_to_date_block(section_body, "2026-07-05", "- 🟡 **[b]** - 证据二")
        self.assertEqual(updated.count("### 2026-07-05"), 1)
        self.assertIn("证据二", updated)
        self.assertLess(updated.index("证据二"), updated.rindex("---"))

    def test_section_without_rule_appends_at_end(self) -> None:
        section_body = "\n### 2026-01-01\n\n- 🟡 **[old]** - 旧证据\n"
        updated = append_to_date_block(section_body, "2026-07-05", "- 🟡 **[new]** - 新证据")
        self.assertIn("### 2026-07-05", updated)
        self.assertLess(updated.index("### 2026-01-01"), updated.index("### 2026-07-05"))


class MissingEnvFileTests(unittest.TestCase):
    """B1: missing env file degrades to a warning instead of crashing."""

    def test_missing_env_file_returns_empty_mapping(self) -> None:
        missing = Path(tempfile.gettempdir()) / "definitely-missing-daily-watch.env"
        self.assertFalse(missing.exists())
        self.assertEqual(load_env_file(missing), {})


if __name__ == "__main__":
    unittest.main()
