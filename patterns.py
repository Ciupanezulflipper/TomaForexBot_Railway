import pandas as pd
import numpy as np
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PatternResult:
    name: str
    strength: str
    bullish: bool
    timestamp: pd.Timestamp

class PatternDetector:
    """Detects basic candlestick patterns without using TA-Lib."""

    @staticmethod
    def detect_patterns(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["Pattern"] = ""
        df["Pattern_Strength"] = ""

        for i in range(2, len(df)):
            o = df.iloc[i]["Open"]
            h = df.iloc[i]["High"]
            l = df.iloc[i]["Low"]
            c = df.iloc[i]["Close"]

            prev_o = df.iloc[i - 1]["Open"]
            prev_c = df.iloc[i - 1]["Close"]
            prev2_c = df.iloc[i - 2]["Close"]

            pattern = ""
            strength = "Medium"
            bullish = None

            # Engulfing
            if c > o and prev_c < prev_o and o < prev_c and c > prev_o:
                pattern = "Engulfing Bullish"
                bullish = True
                strength = "Strong"
            elif c < o and prev_c > prev_o and o > prev_c and c < prev_o:
                pattern = "Engulfing Bearish"
                bullish = False
                strength = "Strong"

            # Doji
            elif abs(c - o) / (h - l + 1e-9) < 0.1:
                pattern = "Doji"
                bullish = None
                strength = "Weak"

            # Hammer
            elif (c > o and (o - l) / (h - l + 1e-9) > 0.6 and (h - c) / (h - l + 1e-9) < 0.2):
                pattern = "Hammer"
                bullish = True
                strength = "Strong"

            # Shooting Star
            elif (c < o and (h - o) / (h - l + 1e-9) > 0.6 and (c - l) / (h - l + 1e-9) < 0.2):
                pattern = "Shooting Star"
                bullish = False
                strength = "Medium"

            # Morning Star (requires 3 candles)
            if i >= 2:
                c1 = df.iloc[i - 2]["Close"]
                o1 = df.iloc[i - 2]["Open"]
                c2 = df.iloc[i - 1]["Close"]
                o2 = df.iloc[i - 1]["Open"]
                if c1 < o1 and abs(c2 - o2) < 0.1 and c > o and c > ((c1 + o1) / 2):
                    pattern = "Morning Star"
                    bullish = True
                    strength = "Strong"

            if pattern:
                direction = "🟢 Bullish" if bullish else "🔴 Bearish" if bullish is False else "⚪ Neutral"
                df.at[df.index[i], "Pattern"] = f"{direction} {pattern}"
                df.at[df.index[i], "Pattern_Strength"] = strength

        return df

    @staticmethod
    def get_recent_patterns(df: pd.DataFrame, lookback_periods: int = 5) -> List[PatternResult]:
        if "Pattern" not in df.columns:
            return []

        recent_df = df.tail(lookback_periods)
        results = []

        for idx, row in recent_df.iterrows():
            text = row["Pattern"]
            if not text or text == "None":
                continue

            bullish = "🟢" in text
            bearish = "🔴" in text
            neutral = "⚪" in text

            pattern_name = text.split(" ", 1)[-1]
            strength = row.get("Pattern_Strength", "Medium")

            results.append(
                PatternResult(
                    name=pattern_name,
                    strength=strength,
                    bullish=True if bullish else False if bearish else None,
                    timestamp=idx if hasattr(idx, "strftime") else pd.Timestamp.now()
                )
            )
        return results

# Main entry for legacy usage
def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    return PatternDetector.detect_patterns(df)
