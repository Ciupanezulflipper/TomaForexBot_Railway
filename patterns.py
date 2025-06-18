# Save as: patterns_test.py
# Run with: python -m unittest patterns_test.py

import unittest
import pandas as pd
from datetime import datetime
from patterns_extended import PatternDetector, PatternResult

class TestPatternDetector(unittest.TestCase):
    def setUp(self):
        # Sample OHLC data for 6 candles
        # We design the 2nd and 4th candle to trigger bullish/bearish engulfing,
        # the 5th for hammer, and the 6th for doji.
        self.df = pd.DataFrame({
            'open':  [10, 9, 11, 12, 10, 8],
            'high':  [11, 10, 13, 13, 12, 9],
            'low':   [8, 8, 10, 10, 8, 7.95],
            'close': [9, 11, 12, 10, 11, 8.05],
        }, index=[
            # Use datetime index for pattern timestamp
            pd.Timestamp("2024-01-01 10:00"),
            pd.Timestamp("2024-01-01 11:00"),
            pd.Timestamp("2024-01-01 12:00"),
            pd.Timestamp("2024-01-01 13:00"),
            pd.Timestamp("2024-01-01 14:00"),
            pd.Timestamp("2024-01-01 15:00"),
        ])

    def test_detect_patterns_multiple(self):
        result = PatternDetector.detect_patterns(self.df)
        self.assertIn('Patterns', result.columns, "'Patterns' column missing.")
        self.assertIn('Pattern_Strengths', result.columns, "'Pattern_Strengths' column missing.")
        # Expect some non-empty pattern cells
        patterns_found = result['Patterns'].fillna("").apply(lambda x: bool(x.strip()))
        self.assertTrue(patterns_found.any(), "No patterns detected in any row.")

    def test_bullish_engulfing(self):
        result = PatternDetector.detect_patterns(self.df)
        # At index 1 (2024-01-01 11:00), bullish engulfing is expected
        patterns = str(result.loc[pd.Timestamp("2024-01-01 11:00"), 'Patterns'])
        self.assertIn("🟢 Bullish Engulfing", patterns, "Bullish engulfing not detected where expected.")

    def test_bearish_engulfing(self):
        result = PatternDetector.detect_patterns(self.df)
        # At index 3 (2024-01-01 13:00), bearish engulfing is expected
        patterns = str(result.loc[pd.Timestamp("2024-01-01 13:00"), 'Patterns'])
        self.assertIn("🔴 Bearish Engulfing", patterns, "Bearish engulfing not detected where expected.")

    def test_hammer(self):
        result = PatternDetector.detect_patterns(self.df)
        # At index 4 (2024-01-01 14:00), hammer is expected
        patterns = str(result.loc[pd.Timestamp("2024-01-01 14:00"), 'Patterns'])
        self.assertIn("🟢 Bullish Hammer", patterns, "Bullish hammer not detected where expected.")

    def test_doji(self):
        result = PatternDetector.detect_patterns(self.df)
        # At index 5 (2024-01-01 15:00), doji is expected
        patterns = str(result.loc[pd.Timestamp("2024-01-01 15:00"), 'Patterns'])
        self.assertIn("Doji", patterns, "Doji not detected where expected.")

    def test_get_recent_patterns(self):
        result = PatternDetector.detect_patterns(self.df)
        patterns = PatternDetector.get_recent_patterns(result, lookback_periods=3)
        self.assertTrue(any(isinstance(p, PatternResult) for p in patterns), "No PatternResult found in recent patterns.")
        # Should find the hammer or doji in last 3
        pattern_names = [p.name for p in patterns]
        self.assertTrue(any("Hammer" in n or "Doji" in n for n in pattern_names), "Hammer or Doji not found in recent patterns.")

    def test_missing_columns(self):
        # Remove 'close' column to test error
        broken_df = self.df.drop(columns=['close'])
        with self.assertRaises(ValueError, msg="ValueError not raised for missing OHLC columns."):
            PatternDetector.detect_patterns(broken_df)

    def test_disable_specific_pattern(self):
        # Only detect Doji: Engulfing & Hammer should not appear
        result = PatternDetector.detect_patterns(self.df, patterns=["Doji"])
        self.assertNotIn("🟢 Bullish Engulfing", result.to_string(), "Bullish Engulfing detected when only Doji enabled.")
        self.assertNotIn("🔴 Bearish Engulfing", result.to_string(), "Bearish Engulfing detected when only Doji enabled.")
        self.assertNotIn("Hammer", result.to_string(), "Hammer detected when only Doji enabled.")
        # Doji should still be present
        patterns = str(result.loc[pd.Timestamp("2024-01-01 15:00"), 'Patterns'])
        self.assertIn("Doji", patterns, "Doji not detected where expected when only Doji is enabled.")

if __name__ == "__main__":
    unittest.main()