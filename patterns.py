# patterns.py (updated with OHLC normalization + DataFrame empty check)

import pandas as pd
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
    @classmethod
    def detect_patterns(cls, df: pd.DataFrame) -> pd.DataFrame:
        result_df = df.copy()

        # ✅ Normalize column names to match expected format
        result_df = result_df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close'
        })

        result_df['Pattern'] = ''
        result_df['Pattern_Strength'] = ''

        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in result_df.columns for col in required_cols):
            logger.error(f"Missing required OHLC columns. Found: {result_df.columns.tolist()}")
            return result_df

        open_prices = result_df['Open'].values
        close_prices = result_df['Close'].values

        patterns = []
        for i in range(1, len(result_df)):
            if close_prices[i] > open_prices[i] and close_prices[i - 1] < open_prices[i - 1]:
                # Bullish Engulfing
                if close_prices[i] > open_prices[i - 1] and open_prices[i] < close_prices[i - 1]:
                    patterns.append((i, 'Engulfing Pattern', 'Strong', True))
            elif close_prices[i] < open_prices[i] and close_prices[i - 1] > open_prices[i - 1]:
                # Bearish Engulfing
                if open_prices[i] > close_prices[i - 1] and close_prices[i] < open_prices[i - 1]:
                    patterns.append((i, 'Engulfing Pattern', 'Strong', False))

        for idx, name, strength, bullish in patterns:
            direction = "🟢 Bullish" if bullish else "🔴 Bearish"
            result_df.at[result_df.index[idx], 'Pattern'] = f"{direction} {name}"
            result_df.at[result_df.index[idx], 'Pattern_Strength'] = strength

        logger.info(f"Detected {len(patterns)} engulfing patterns across {len(result_df)} candles")
        return result_df

    @classmethod
    def get_recent_patterns(cls, df: pd.DataFrame, lookback_periods: int = 3) -> List[PatternResult]:
        try:
            if 'Pattern' not in df.columns:
                return []

            recent_df = df.tail(lookback_periods)
            patterns = []

            for idx, row in recent_df.iterrows():
                if row['Pattern'] and row['Pattern'].strip():
                    parts = row['Pattern'].split('|')
                    for part in parts:
                        part = part.strip()
                        if part:
                            is_bullish = "🟢 Bullish" in part
                            name = part.replace("🟢 Bullish ", "").replace("🔴 Bearish ", "")
                            patterns.append(PatternResult(
                                name=name,
                                strength=row.get('Pattern_Strength', 'Medium'),
                                bullish=is_bullish,
                                timestamp=idx if hasattr(idx, 'strftime') else pd.Timestamp.now()
                            ))
            return patterns

        except Exception as e:
            logger.error(f"Error extracting recent patterns: {e}")
            return []

def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    return PatternDetector.detect_patterns(df)

detect_patterns = PatternDetector.detect_patterns
