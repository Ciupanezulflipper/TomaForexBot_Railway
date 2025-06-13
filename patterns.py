import pandas as pd
import numpy as np
import talib
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PatternResult:
    """Data class to hold pattern detection results"""
    name: str
    strength: str
    bullish: bool
    timestamp: pd.Timestamp

class PatternDetector:
    """Enhanced pattern detector"""

    BULLISH_PATTERNS = {
        'CDLENGULFING': ('Engulfing Pattern', 'Strong'),
        'CDLHAMMER': ('Hammer', 'Strong'),
        'CDLMORNINGSTAR': ('Morning Star', 'Strong'),
        'CDLDOJI': ('Doji', 'Weak'),
        'CDLSHOOTINGSTAR': ('Shooting Star', 'Medium'),
        'CDLHARAMI': ('Harami Pattern', 'Medium'),
        'CDLPIERCING': ('Piercing Pattern', 'Strong'),
        'CDLDARKCLOUDCOVER': ('Dark Cloud Cover', 'Strong'),
        'CDL3WHITESOLDIERS': ('Three Advancing White Soldiers', 'Strong'),
        'CDL3BLACKCROWS': ('Three Black Crows', 'Strong'),
    }

    @classmethod
    def detect_patterns(cls, df: pd.DataFrame) -> pd.DataFrame:
        try:
            result_df = df.copy()
            result_df['Pattern'] = ''
            result_df['Pattern_Strength'] = ''

            required_cols = ['Open', 'High', 'Low', 'Close']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required OHLC columns. Found: {df.columns.tolist()}")
                return result_df

            open_prices = df['Open'].values
            high_prices = df['High'].values
            low_prices = df['Low'].values
            close_prices = df['Close'].values

            detected_patterns = []

            for pattern_func, (pattern_name, strength) in cls.BULLISH_PATTERNS.items():
                try:
                    talib_func = getattr(talib, pattern_func)
                    pattern_result = talib_func(open_prices, high_prices, low_prices, close_prices)
                    pattern_indices = np.where(pattern_result != 0)[0]

                    for idx in pattern_indices:
                        signal_value = pattern_result[idx]
                        is_bullish = signal_value > 0
                        detected_patterns.append({
                            'index': idx,
                            'pattern': pattern_name,
                            'strength': strength,
                            'bullish': is_bullish
                        })
                except Exception as e:
                    logger.warning(f"Error detecting pattern {pattern_func}: {str(e)}")
                    continue

            for pattern_info in detected_patterns:
                idx = pattern_info['index']
                direction = "🟢 Bullish" if pattern_info['bullish'] else "🔴 Bearish"
                pattern_text = f"{direction} {pattern_info['pattern']}"

                if result_df.iloc[idx]['Pattern']:
                    result_df.iloc[idx, result_df.columns.get_loc('Pattern')] += f" | {pattern_text}"
                else:
                    result_df.iloc[idx, result_df.columns.get_loc('Pattern')] = pattern_text

                result_df.iloc[idx, result_df.columns.get_loc('Pattern_Strength')] = pattern_info['strength']

            logger.info(f"Detected {len(detected_patterns)} pattern signals across {len(df)} candles")
            return result_df

        except Exception as e:
            logger.error(f"Error in pattern detection: {str(e)}")
            result_df = df.copy()
            result_df['Pattern'] = ''
            result_df['Pattern_Strength'] = ''
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
                    pattern_parts = row['Pattern'].split('|')

                    for pattern_part in pattern_parts:
                        pattern_part = pattern_part.strip()
                        if pattern_part:
                            is_bullish = "🟢 Bullish" in pattern_part
                            pattern_name = pattern_part.replace("🟢 Bullish ", "").replace("🔴 Bearish ", "")
                            patterns.append(PatternResult(
                                name=pattern_name,
                                strength=row.get('Pattern_Strength', 'Medium'),
                                bullish=is_bullish,
                                timestamp=idx if hasattr(idx, 'strftime') else pd.Timestamp.now()
                            ))

            return patterns

        except Exception as e:
            logger.error(f"Error extracting recent patterns: {str(e)}")
            return []

# Main compatibility wrapper
def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    return PatternDetector.detect_patterns(df)
