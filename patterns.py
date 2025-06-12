import pandas as pd
import numpy as np
import talib
import logging
from typing import Dict, List, Tuple, Optional
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
    """Enhanced pattern detector with better organization"""
    
    # Pattern mappings with strength indicators
    BULLISH_PATTERNS = {
        'CDL2CROWS': ('Two Crows', 'Medium'),
        'CDL3BLACKCROWS': ('Three Black Crows', 'Strong'),
        'CDL3INSIDE': ('Three Inside Up/Down', 'Medium'),
        'CDL3LINESTRIKE': ('Three-Line Strike', 'Strong'),
        'CDL3OUTSIDE': ('Three Outside Up/Down', 'Medium'),
        'CDL3STARSINSOUTH': ('Three Stars In The South', 'Medium'),
        'CDL3WHITESOLDIERS': ('Three Advancing White Soldiers', 'Strong'),
        'CDLABANDONEDBABY': ('Abandoned Baby', 'Strong'),
        'CDLADVANCEBLOCK': ('Advance Block', 'Medium'),
        'CDLBELTHOLD': ('Belt-hold', 'Medium'),
        'CDLBREAKAWAY': ('Breakaway', 'Medium'),
        'CDLCLOSINGMARUBOZU': ('Closing Marubozu', 'Medium'),
        'CDLCONCEALBABYSWALL': ('Concealing Baby Swallow', 'Medium'),
        'CDLCOUNTERATTACK': ('Counterattack', 'Medium'),
        'CDLDARKCLOUDCOVER': ('Dark Cloud Cover', 'Strong'),
        'CDLDOJI': ('Doji', 'Weak'),
        'CDLDOJISTAR': ('Doji Star', 'Medium'),
        'CDLDRAGONFLYDOJI': ('Dragonfly Doji', 'Medium'),
        'CDLENGULFING': ('Engulfing Pattern', 'Strong'),
        'CDLEVENINGDOJISTAR': ('Evening Doji Star', 'Strong'),
        'CDLEVENINGSTAR': ('Evening Star', 'Strong'),
        'CDLGAPSIDESIDEWHITE': ('Up/Down-gap side-by-side white lines', 'Medium'),
        'CDLGRAVESTONEDOJI': ('Gravestone Doji', 'Medium'),
        'CDLHAMMER': ('Hammer', 'Strong'),
        'CDLHANGINGMAN': ('Hanging Man', 'Medium'),
        'CDLHARAMI': ('Harami Pattern', 'Medium'),
        'CDLHARAMICROSS': ('Harami Cross Pattern', 'Medium'),
        'CDLHIGHWAVE': ('High-Wave Candle', 'Weak'),
        'CDLHIKKAKE': ('Hikkake Pattern', 'Medium'),
        'CDLHIKKAKEMOD': ('Modified Hikkake Pattern', 'Medium'),
        'CDLHOMINGPIGEON': ('Homing Pigeon', 'Medium'),
        'CDLIDENTICAL3CROWS': ('Identical Three Crows', 'Strong'),
        'CDLINNECK': ('In-Neck Pattern', 'Weak'),
        'CDLINVERTEDHAMMER': ('Inverted Hammer', 'Medium'),
        'CDLKICKING': ('Kicking', 'Strong'),
        'CDLKICKINGBYLENGTH': ('Kicking - bull/bear determined by the longer marubozu', 'Strong'),
        'CDLLADDERBOTTOM': ('Ladder Bottom', 'Strong'),
        'CDLLONGLEGGEDDOJI': ('Long Legged Doji', 'Medium'),
        'CDLLONGLINE': ('Long Line Candle', 'Medium'),
        'CDLMARUBOZU': ('Marubozu', 'Medium'),
        'CDLMATCHINGLOW': ('Matching Low', 'Medium'),
        'CDLMATHOLD': ('Mat Hold', 'Medium'),
        'CDLMORNINGDOJISTAR': ('Morning Doji Star', 'Strong'),
        'CDLMORNINGSTAR': ('Morning Star', 'Strong'),
        'CDLONNECK': ('On-Neck Pattern', 'Weak'),
        'CDLPIERCING': ('Piercing Pattern', 'Strong'),
        'CDLRICKSHAWMAN': ('Rickshaw Man', 'Weak'),
        'CDLRISEFALL3METHODS': ('Rising/Falling Three Methods', 'Medium'),
        'CDLSEPARATINGLINES': ('Separating Lines', 'Medium'),
        'CDLSHOOTINGSTAR': ('Shooting Star', 'Medium'),
        'CDLSHORTLINE': ('Short Line Candle', 'Weak'),
        'CDLSPINNINGTOP': ('Spinning Top', 'Weak'),
        'CDLSTALLEDPATTERN': ('Stalled Pattern', 'Medium'),
        'CDLSTICKSANDWICH': ('Stick Sandwich', 'Medium'),
        'CDLTAKURI': ('Takuri (Dragonfly Doji with very long lower shadow)', 'Medium'),
        'CDLTASUKIGAP': ('Tasuki Gap', 'Medium'),
        'CDLTHRUSTING': ('Thrusting Pattern', 'Weak'),
        'CDLTRISTAR': ('Tristar Pattern', 'Strong'),
        'CDLUNIQUE3RIVER': ('Unique 3 River', 'Medium'),
        'CDLUPSIDEGAP2CROWS': ('Upside Gap Two Crows', 'Medium'),
        'CDLXSIDEGAP3METHODS': ('Upside/Downside Gap Three Methods', 'Medium')
    }

    @classmethod
    def detect_patterns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect candlestick patterns and return DataFrame with pattern annotations
        
        Args:
            df: DataFrame with OHLC data (columns: Open, High, Low, Close)
            
        Returns:
            DataFrame with added 'Pattern' and 'Pattern_Strength' columns
        """
        try:
            # Create a copy to avoid modifying the original
            result_df = df.copy()
            
            # Initialize pattern columns
            result_df['Pattern'] = ''
            result_df['Pattern_Strength'] = ''
            
            # Validate required columns
            required_cols = ['Open', 'High', 'Low', 'Close']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required OHLC columns. Found: {df.columns.tolist()}")
                return result_df
                
            # Convert to numpy arrays for TA-Lib
            open_prices = df['Open'].values
            high_prices = df['High'].values  
            low_prices = df['Low'].values
            close_prices = df['Close'].values
            
            # Detect all patterns
            detected_patterns = []
            
            for pattern_func, (pattern_name, strength) in cls.BULLISH_PATTERNS.items():
                try:
                    # Get the TA-Lib function
                    talib_func = getattr(talib, pattern_func)
                    
                    # Calculate pattern
                    pattern_result = talib_func(open_prices, high_prices, low_prices, close_prices)
                    
                    # Find where patterns occur (non-zero values)
                    pattern_indices = np.where(pattern_result != 0)[0]
                    
                    for idx in pattern_indices:
                        # Determine if bullish or bearish based on TA-Lib result
                        signal_value = pattern_result[idx]
                        is_bullish = signal_value > 0
                        
                        detected_patterns.append({
                            'index': idx,
                            'pattern': pattern_name,
                            'strength': strength,
                            'bullish': is_bullish,
                            'signal_value': signal_value
                        })
                        
                except Exception as e:
                    logger.warning(f"Error detecting pattern {pattern_func}: {str(e)}")
                    continue
            
            # Apply patterns to DataFrame
            for pattern_info in detected_patterns:
                idx = pattern_info['index']
                direction = "🟢 Bullish" if pattern_info['bullish'] else "🔴 Bearish"
                pattern_text = f"{direction} {pattern_info['pattern']}"
                
                # If there's already a pattern at this index, combine them
                if result_df.iloc[idx]['Pattern']:
                    result_df.iloc[idx, result_df.columns.get_loc('Pattern')] += f" | {pattern_text}"
                else:
                    result_df.iloc[idx, result_df.columns.get_loc('Pattern')] = pattern_text
                    
                result_df.iloc[idx, result_df.columns.get_loc('Pattern_Strength')] = pattern_info['strength']
            
            logger.info(f"Detected {len(detected_patterns)} pattern signals across {len(df)} candles")
            return result_df
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {str(e)}")
            # Return original DataFrame with empty pattern columns
            result_df = df.copy()
            result_df['Pattern'] = ''
            result_df['Pattern_Strength'] = ''
            return result_df

    @classmethod
    def get_recent_patterns(cls, df: pd.DataFrame, lookback_periods: int = 5) -> List[PatternResult]:
        """
        Extract recent patterns from annotated DataFrame
        
        Args:
            df: DataFrame with Pattern and Pattern_Strength columns
            lookback_periods: Number of recent periods to check
            
        Returns:
            List of PatternResult objects for recent patterns
        """
        try:
            if 'Pattern' not in df.columns:
                return []
                
            # Get recent data
            recent_df = df.tail(lookback_periods)
            patterns = []
            
            for idx, row in recent_df.iterrows():
                if row['Pattern'] and row['Pattern'].strip():
                    # Handle multiple patterns separated by |
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

@dataclass
class PatternResult:
    """Simple representation of a detected candle pattern."""

    name: str
    bullish: bool
    strength: str = "medium"


class PatternDetector:
    """Utility helpers for working with candle patterns."""

    @staticmethod
    def get_recent_patterns(df: pd.DataFrame, lookback_periods: int = 3) -> List[PatternResult]:
        """Return PatternResult objects from the last ``lookback_periods`` rows."""
        if "Pattern" not in df.columns:
            return []

        recent = df.tail(lookback_periods)
        results: List[PatternResult] = []

        for pattern_name in recent["Pattern"]:
            if not pattern_name or pattern_name == "None":
                continue

            name = str(pattern_name)
            lower = name.lower()
            bullish = "bullish" in lower

            if "engulfing" in lower:
                strength = "strong"
            else:
                strength = "medium"

            results.append(PatternResult(name=name, bullish=bullish, strength=strength))

        return results

            
        except Exception as e:
            logger.error(f"Error extracting recent patterns: {str(e)}")
            return []

# Main function for backward compatibility
def detect_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main function to detect candlestick patterns
    
    Args:
        df: DataFrame with OHLC data
        
    Returns:
        DataFrame with pattern annotations
        
    Note: max_patterns parameter has been removed
    """
    return PatternDetector.detect_patterns(df)