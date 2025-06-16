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
    @classmethod
    def detect_patterns(cls, df: pd.DataFrame) -> pd.DataFrame:
        try:
            df = df.copy()
            df.columns = [col.lower() for col in df.columns]

            result_df = df.copy()
            result_df['pattern'] = ''
            result_df['pattern_strength'] = ''

            open_prices = df['open'].values
            close_prices = df['close'].values
            high_prices = df['high'].values
            low_prices = df['low'].values

            for i in range(1, len(df)):
                patterns = []

                # Engulfing Pattern
                if close_prices[i] > open_prices[i] and close_prices[i - 1] < open_prices[i - 1]:
                    if close_prices[i] > open_prices[i - 1] and open_prices[i] < close_prices[i - 1]:
                        patterns.append(('Engulfing Pattern', 'Strong', True))

                elif close_prices[i] < open_prices[i] and close_prices[i - 1] > open_prices[i - 1]:
                    if open_prices[i] > close_prices[i - 1] and close_prices[i] < open_prices[i - 1]:
                        patterns.append(('Engulfing Pattern', 'Strong', False))

                # Hammer
                body = abs(close_prices[i] - open_prices[i])
                range_total = high_prices[i] - low_prices[i]
                lower_shadow = open_prices[i] - low_prices[i] if close_prices[i] > open_prices[i] else close_prices[i] - low_prices[i]

                if body < range_total * 0.3 and lower_shadow > body * 2:
                    patterns.append(('Hammer', 'Medium', True))

                # Shooting Star
                upper_shadow = high_prices[i] - close_prices[i] if close_prices[i] > open_prices[i] else high_prices[i] - open_prices[i]
                if body < range_total * 0.3 and upper_shadow > body * 2:
                    patterns.append(('Shooting Star', 'Medium', False))

                # Doji
                if abs(close_prices[i] - open_prices[i]) < (high_prices[i] - low_prices[i]) * 0.1:
                    patterns.append(('Doji', 'Weak', None))

                if patterns:
                    texts = []
                    for name, strength, bullish in patterns:
                        if bullish is True:
                            texts.append(f"🟢 Bullish {name}")
                        elif bullish is False:
                            texts.append(f"🔴 Bearish {name}")
                        else:
                            texts.append(f"⚪ Neutral {name}")

                    result_df.at[result_df.index[i], 'pattern'] = ' | '.join(texts)
                    result_df.at[result_df.index[i], 'pattern_strength'] = patterns[0][1]

            return result_df

        except Exception as e:
            logger.error(f"Error in pattern detection: {str(e)}")
            result_df = df.copy()
            result_df['pattern'] = ''
            result_df['pattern_strength'] = ''
            return result_df

    @classmethod
    def get_recent_patterns(cls, df: pd.DataFrame, lookback_periods: int = 3) -> List[PatternResult]:
        try:
            if 'pattern' not in df.columns:
                return []

            recent_df = df.tail(lookback_periods)
            patterns = []

            for idx, row in recent_df.iterrows():
                if row['pattern'] and str(row['pattern']).strip():
                    parts = str(row['pattern']).split('|')
                    for part in parts:
                        part = part.strip()
                        if part:
                            is_bullish = "🟢 Bullish" in part
                            is_bearish = "🔴 Bearish" in part
                            name = part.replace("🟢 Bullish ", "").replace("🔴 Bearish ", "").replace("⚪ Neutral ", "")
                            patterns.append(PatternResult(
                                name=name,
                                strength=row.get('pattern_strength', 'Medium'),
                                bullish=True if is_bullish else False if is_bearish else None,
                                timestamp=idx if hasattr(idx, 'strftime') else pd.Timestamp.now()
                            ))
            return patterns

        except Exception as e:
            logger.error(f"Error extracting recent patterns: {str(e)}")
            return []

def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    return PatternDetector.detect_patterns(df)

detect_patterns = PatternDetector.detect_patterns
