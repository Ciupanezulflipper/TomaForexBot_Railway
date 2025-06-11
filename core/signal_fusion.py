"""
Advanced Signal Fusion Module for TomaForexBot
Combines Technical Analysis, Pattern Recognition, News Sentiment, and Market Structure
"""

import logging
import asyncio
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class AdvancedSignalFusion:
    """
    Advanced trading signal fusion system with multi-timeframe analysis
    """
    
    def __init__(self):
        # Signal weights (must sum to 1.0)
        self.weights = {
            'technical_indicators': 0.35,
            'candlestick_patterns': 0.25,
            'news_sentiment': 0.20,
            'market_structure': 0.15,
            'volume_analysis': 0.05
        }
        
        # Confidence thresholds
        self.min_confidence = 0.65  # Minimum score to confirm signal
        self.strong_confidence = 0.80  # Strong signal threshold
        
        # Risk management
        self.max_daily_signals = 10
        self.signal_cooldown = 300  # 5 minutes between signals for same pair
        
        # Cache for recent signals
        self.recent_signals = {}
    
    async def get_technical_indicators(self, symbol: str, timeframe: str = "H1") -> Dict:
        """
        Comprehensive technical indicator analysis
        """
        try:
            # Import your existing modules
            from marketdata import get_ohlc
            from indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands
            
            df = await get_ohlc(symbol, timeframe)
            if df is None or df.empty:
                return self._empty_signal("No market data available")
            
            signals = []
            score = 0.0
            strength = 0
            
            # === RSI Analysis ===
            try:
                rsi = calculate_rsi(df['close'], 14)
                current_rsi = rsi.iloc[-1] if not rsi.empty else 50
                
                if current_rsi <= 25:  # Extremely oversold
                    signals.append(f"RSI Extremely Oversold ({current_rsi:.1f}) - Strong BUY")
                    score += 3.0
                    strength += 2
                elif current_rsi <= 35:  # Oversold
                    signals.append(f"RSI Oversold ({current_rsi:.1f}) - BUY")
                    score += 2.0
                    strength += 1
                elif current_rsi >= 75:  # Extremely overbought
                    signals.append(f"RSI Extremely Overbought ({current_rsi:.1f}) - Strong SELL")
                    score -= 3.0
                    strength += 2
                elif current_rsi >= 65:  # Overbought
                    signals.append(f"RSI Overbought ({current_rsi:.1f}) - SELL")
                    score -= 2.0
                    strength += 1
                
            except Exception as e:
                logger.warning(f"RSI calculation failed for {symbol}: {e}")
            
            # === MACD Analysis ===
            try:
                macd_line, signal_line, histogram = calculate_macd(df['close'])
                if len(macd_line) > 2:
                    current_macd = macd_line.iloc[-1]
                    current_signal = signal_line.iloc[-1]
                    prev_macd = macd_line.iloc[-2]
                    prev_signal = signal_line.iloc[-2]
                    
                    # Bullish crossover
                    if current_macd > current_signal and prev_macd <= prev_signal:
                        signals.append("MACD Bullish Crossover - BUY")
                        score += 2.5
                        strength += 2
                    # Bearish crossover
                    elif current_macd < current_signal and prev_macd >= prev_signal:
                        signals.append("MACD Bearish Crossover - SELL")
                        score -= 2.5
                        strength += 2
                    # Divergence analysis
                    elif current_macd > 0 and current_macd > prev_macd:
                        signals.append("MACD Bullish Momentum")
                        score += 1.0
                    elif current_macd < 0 and current_macd < prev_macd:
                        signals.append("MACD Bearish Momentum")
                        score -= 1.0
                        
            except Exception as e:
                logger.warning(f"MACD calculation failed for {symbol}: {e}")
            
            # === Bollinger Bands Analysis ===
            try:
                bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df['close'], 20, 2)
                current_price = df['close'].iloc[-1]
                bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
                
                if bb_position <= 0.1:  # Near lower band
                    signals.append(f"Price at Lower Bollinger Band ({bb_position:.2f}) - BUY")
                    score += 2.0
                    strength += 1
                elif bb_position >= 0.9:  # Near upper band
                    signals.append(f"Price at Upper Bollinger Band ({bb_position:.2f}) - SELL")
                    score -= 2.0
                    strength += 1
                elif bb_position <= 0.3:
                    signals.append("Price in Lower BB Zone - Weak BUY")
                    score += 1.0
                elif bb_position >= 0.7:
                    signals.append("Price in Upper BB Zone - Weak SELL")
                    score -= 1.0
                    
            except Exception as e:
                logger.warning(f"Bollinger Bands calculation failed for {symbol}: {e}")
            
            # === Moving Average Analysis ===
            try:
                ma_short = df['close'].rolling(window=9).mean()
                ma_long = df['close'].rolling(window=21).mean()
                current_price = df['close'].iloc[-1]
                
                if current_price > ma_short.iloc[-1] > ma_long.iloc[-1]:
                    signals.append("Price Above Moving Averages - BUY")
                    score += 1.5
                elif current_price < ma_short.iloc[-1] < ma_long.iloc[-1]:
                    signals.append("Price Below Moving Averages - SELL")
                    score -= 1.5
                    
            except Exception as e:
                logger.warning(f"Moving Average calculation failed for {symbol}: {e}")
            
            return {
                "score": score,
                "signals": signals,
                "strength": strength,
                "reason": "; ".join(signals) if signals else "No clear technical signals",
                "details": {
                    "rsi": current_rsi if 'current_rsi' in locals() else None,
                    "macd_signal": "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
                }
            }
            
        except Exception as e:
            logger.error(f"Technical indicator analysis failed for {symbol}: {e}")
            return self._empty_signal(f"Technical analysis error: {str(e)}")
    
    async def get_candlestick_patterns(self, symbol: str, timeframe: str = "H1") -> Dict:
        """
        Advanced candlestick pattern recognition with strength scoring
        """
        try:
            from marketdata import get_ohlc
            from patterns import detect_candle_patterns
            
            df = await get_ohlc(symbol, timeframe)
            if df is None or df.empty:
                return self._empty_signal("No data for pattern analysis")
            
            df_with_patterns = detect_candle_patterns(df)
            
            # Get last few candles for pattern confirmation
            last_patterns = df_with_patterns.tail(3)['Pattern'].tolist() if 'Pattern' in df_with_patterns.columns else []
            current_pattern = last_patterns[-1] if last_patterns else ""
            
            score = 0.0
            signals = []
            strength = 0
            
            # === Bullish Patterns ===
            bullish_patterns = {
                'Hammer': 2.0,
                'Bullish Engulfing': 3.0,
                'Morning Star': 3.5,
                'Piercing Line': 2.5,
                'Three White Soldiers': 4.0,
                'Doji': 1.0,  # Indecision, but potential reversal
                'Dragonfly Doji': 2.5
            }
            
            # === Bearish Patterns ===
            bearish_patterns = {
                'Shooting Star': 2.0,
                'Bearish Engulfing': 3.0,
                'Evening Star': 3.5,
                'Dark Cloud Cover': 2.5,
                'Three Black Crows': 4.0,
                'Gravestone Doji': 2.5,
                'Hanging Man': 1.5
            }
            
            # Check for bullish patterns
            for pattern, pattern_score in bullish_patterns.items():
                if pattern in current_pattern:
                    signals.append(f"{pattern} - BUY Signal")
                    score += pattern_score
                    strength += int(pattern_score / 2)
                    break
            
            # Check for bearish patterns
            for pattern, pattern_score in bearish_patterns.items():
                if pattern in current_pattern:
                    signals.append(f"{pattern} - SELL Signal")
                    score -= pattern_score
                    strength += int(pattern_score / 2)
                    break
            
            # Pattern confirmation with previous candles
            if len(last_patterns) >= 2:
                prev_pattern = last_patterns[-2]
                if current_pattern and prev_pattern:
                    if any(bp in current_pattern for bp in bullish_patterns) and any(bp in prev_pattern for bp in bullish_patterns):
                        signals.append("Pattern Confirmation - Enhanced BUY")
                        score += 1.0
                        strength += 1
                    elif any(bp in current_pattern for bp in bearish_patterns) and any(bp in prev_pattern for bp in bearish_patterns):
                        signals.append("Pattern Confirmation - Enhanced SELL")
                        score -= 1.0
                        strength += 1
            
            return {
                "score": score,
                "signals": signals,
                "strength": strength,
                "reason": "; ".join(signals) if signals else "No significant patterns detected",
                "details": {
                    "current_pattern": current_pattern,
                    "pattern_history": last_patterns
                }
            }
            
        except Exception as e:
            logger.error(f"Pattern analysis failed for {symbol}: {e}")
            return self._empty_signal(f"Pattern analysis error: {str(e)}")
    
    async def get_news_sentiment(self, symbol: str) -> Dict:
        """
        News sentiment analysis with impact scoring
        """
        try:
            from news_fetcher import fetch_combined_news
            from news_signal_logic import analyze_multiple_headlines
            
            headlines = await fetch_combined_news()
            if not headlines:
                return self._empty_signal("No news data available")
            
            # Filter news relevant to the symbol
            symbol_news = [h for h in headlines if symbol.replace('USD', '').replace('EUR', '').replace('GBP', '') in h.upper()]
            
            # Analyze all news for broader market sentiment
            all_news_result = analyze_multiple_headlines(headlines, symbol)
            
            # Analyze symbol-specific news
            symbol_result = analyze_multiple_headlines(symbol_news, symbol) if symbol_news else {"score": 0, "reasons": []}
            
            # Combine scores with weights
            general_weight = 0.3
            specific_weight = 0.7
            
            combined_score = (all_news_result.get("score", 0) * general_weight + 
                            symbol_result.get("score", 0) * specific_weight)
            
            signals = []
            strength = 0
            
            if combined_score >= 2:
                signals.append(f"Strong Positive News Sentiment ({combined_score:.1f})")
                strength = 3
            elif combined_score >= 1:
                signals.append(f"Positive News Sentiment ({combined_score:.1f})")
                strength = 2
            elif combined_score <= -2:
                signals.append(f"Strong Negative News Sentiment ({combined_score:.1f})")
                strength = 3
            elif combined_score <= -1:
                signals.append(f"Negative News Sentiment ({combined_score:.1f})")
                strength = 2
            
            # Add specific reasons
            all_reasons = all_news_result.get("reasons", []) + symbol_result.get("reasons", [])
            
            return {
                "score": combined_score,
                "signals": signals,
                "strength": strength,
                "reason": "; ".join(signals) if signals else "Neutral news sentiment",
                "details": {
                    "general_sentiment": all_news_result.get("score", 0),
                    "specific_sentiment": symbol_result.get("score", 0),
                    "news_reasons": all_reasons[:5]  # Top 5 reasons
                }
            }
            
        except Exception as e:
            logger.error(f"News sentiment analysis failed for {symbol}: {e}")
            return self._empty_signal(f"News analysis error: {str(e)}")
    
    async def get_market_structure(self, symbol: str, timeframe: str = "H1") -> Dict:
        """
        Market structure analysis - support/resistance, trend strength
        """
        try:
            from marketdata import get_ohlc
            
            df = await get_ohlc(symbol, timeframe)
            if df is None or df.empty:
                return self._empty_signal("No data for market structure analysis")
            
            signals = []
            score = 0.0
            strength = 0
            
            # === Trend Analysis ===
            # Simple trend using price vs moving averages
            if len(df) >= 50:
                ma_20 = df['close'].rolling(window=20).mean()
                ma_50 = df['close'].rolling(window=50).mean()
                current_price = df['close'].iloc[-1]
                
                if current_price > ma_20.iloc[-1] > ma_50.iloc[-1]:
                    signals.append("Strong Uptrend Structure")
                    score += 2.0
                    strength += 2
                elif current_price < ma_20.iloc[-1] < ma_50.iloc[-1]:
                    signals.append("Strong Downtrend Structure")
                    score -= 2.0
                    strength += 2
                elif current_price > ma_20.iloc[-1]:
                    signals.append("Weak Uptrend Structure")
                    score += 1.0
                    strength += 1
                elif current_price < ma_20.iloc[-1]:
                    signals.append("Weak Downtrend Structure")
                    score -= 1.0
                    strength += 1
            
            # === Support/Resistance Analysis ===
            # Find recent highs and lows
            recent_data = df.tail(20)
            if len(recent_data) >= 10:
                recent_high = recent_data['high'].max()
                recent_low = recent_data['low'].min()
                current_price = df['close'].iloc[-1]
                
                # Distance from recent high/low
                distance_from_high = (recent_high - current_price) / recent_high
                distance_from_low = (current_price - recent_low) / recent_low
                
                if distance_from_low < 0.01:  # Very close to recent low
                    signals.append("Near Recent Support Level - BUY")
                    score += 1.5
                    strength += 1
                elif distance_from_high < 0.01:  # Very close to recent high
                    signals.append("Near Recent Resistance Level - SELL")
                    score -= 1.5
                    strength += 1
            
            return {
                "score": score,
                "signals": signals,
                "strength": strength,
                "reason": "; ".join(signals) if signals else "Neutral market structure",
                "details": {
                    "trend": "bullish" if score > 0 else "bearish" if score < 0 else "sideways",
                    "structure_strength": strength
                }
            }
            
        except Exception as e:
            logger.error(f"Market structure analysis failed for {symbol}: {e}")
            return self._empty_signal(f"Market structure error: {str(e)}")
    
    async def get_volume_analysis(self, symbol: str, timeframe: str = "H1") -> Dict:
        """
        Volume analysis for signal confirmation
        """
        try:
            from marketdata import get_ohlc
            
            df = await get_ohlc(symbol, timeframe)
            if df is None or df.empty or 'volume' not in df.columns:
                return self._empty_signal("No volume data available")
            
            signals = []
            score = 0.0
            strength = 0
            
            # Volume moving average
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume_ma'].iloc[-1]
            
            # Price change
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            
            # Volume confirmation
            if current_volume > avg_volume * 1.5:  # High volume
                if price_change > 0:
                    signals.append("High Volume Bullish Confirmation")
                    score += 1.0
                    strength += 1
                elif price_change < 0:
                    signals.append("High Volume Bearish Confirmation")
                    score -= 1.0
                    strength += 1
            
            return {
                "score": score,
                "signals": signals,
                "strength": strength,
                "reason": "; ".join(signals) if signals else "Normal volume activity",
                "details": {
                    "current_volume": current_volume,
                    "average_volume": avg_volume,
                    "volume_ratio": current_volume / avg_volume if avg_volume > 0 else 1
                }
            }
            
        except Exception as e:
            logger.error(f"Volume analysis failed for {symbol}: {e}")
            return self._empty_signal("Volume data not available")
    
    def _empty_signal(self, reason: str) -> Dict:
        """Return empty signal structure"""
        return {
            "score": 0.0,
            "signals": [],
            "strength": 0,
            "reason": reason,
            "details": {}
        }
    
    def calculate_final_score(self, all_signals: Dict) -> Tuple[float, str, int]:
        """
        Calculate weighted final score and determine signal direction
        """
        total_score = 0.0
        total_strength = 0
        
        # Apply weights to each signal component
        for signal_type, weight in self.weights.items():
            if signal_type in all_signals:
                signal_data = all_signals[signal_type]
                total_score += signal_data.get('score', 0) * weight
                total_strength += signal_data.get('strength', 0)
        
        # Normalize strength
        max_possible_strength = sum(3 for _ in self.weights)  # Max strength per component is 3
        strength_percentage = min(total_strength / max_possible_strength, 1.0) if max_possible_strength > 0 else 0
        
        # Determine signal direction
        if total_score >= self.strong_confidence:
            return total_score, "STRONG_BUY", int(strength_percentage * 100)
        elif total_score >= self.min_confidence:
            return total_score, "BUY", int(strength_percentage * 100)
        elif total_score <= -self.strong_confidence:
            return abs(total_score), "STRONG_SELL", int(strength_percentage * 100)
        elif total_score <= -self.min_confidence:
            return abs(total_score), "SELL", int(strength_percentage * 100)
        else:
            return abs(total_score), "HOLD", int(strength_percentage * 100)
    
    def check_signal_cooldown(self, symbol: str) -> bool:
        """Check if enough time has passed since last signal for this symbol"""
        if symbol not in self.recent_signals:
            return True
        
        last_signal_time = self.recent_signals[symbol]
        return (datetime.now() - last_signal_time).total_seconds() > self.signal_cooldown
    
    def record_signal(self, symbol: str):
        """Record timestamp of signal for cooldown tracking"""
        self.recent_signals[symbol] = datetime.now()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN FUNCTIONS EXPECTED BY YOUR BOT
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_trade_decision(symbol: str, chat_id: int = None) -> Dict:
    """
    Main function to generate comprehensive trading decisions
    
    Args:
        symbol: Trading pair (e.g., 'EURUSD')
        chat_id: Telegram chat ID (optional)
    
    Returns:
        Dict with keys: confirmed, signal, avg_score, reason, strength, details
    """
    try:
        fusion = AdvancedSignalFusion()
        
        # Check cooldown
        if not fusion.check_signal_cooldown(symbol):
            return {
                "confirmed": False,
                "signal": "COOLDOWN",
                "avg_score": 0,
                "reason": f"Signal cooldown active for {symbol}",
                "strength": 0,
                "details": {}
            }
        
        logger.info(f"Starting comprehensive analysis for {symbol}")
        
        # Gather all signal components
        tasks = [
            fusion.get_technical_indicators(symbol),
            fusion.get_candlestick_patterns(symbol),
            fusion.get_news_sentiment(symbol),
            fusion.get_market_structure(symbol),
            fusion.get_volume_analysis(symbol)
        ]
        
        # Execute all analyses concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to signal types
        signal_types = ['technical_indicators', 'candlestick_patterns', 'news_sentiment', 
                       'market_structure', 'volume_analysis']
        
        all_signals = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in {signal_types[i]} analysis: {result}")
                all_signals[signal_types[i]] = fusion._empty_signal(f"Error: {str(result)}")
            else:
                all_signals[signal_types[i]] = result
        
        # Calculate final weighted decision
        final_score, signal_direction, strength = fusion.calculate_final_score(all_signals)
        
        # Compile comprehensive reason
        reasons = []
        for signal_type, signal_data in all_signals.items():
            if signal_data.get('reason') and signal_data['reason'] != f"No clear {signal_type} signals":
                reasons.append(f"{signal_type.replace('_', ' ').title()}: {signal_data['reason']}")
        
        # Determine if signal is confirmed
        confirmed = signal_direction not in ["HOLD", "COOLDOWN"] and final_score >= fusion.min_confidence
        
        # Record signal if confirmed
        if confirmed:
            fusion.record_signal(symbol)
        
        # Prepare final result
        result = {
            "confirmed": confirmed,
            "signal": signal_direction,
            "avg_score": final_score,
            "reason": " | ".join(reasons) if reasons else "No clear signals detected",
            "strength": strength,
            "details": {
                "individual_signals": all_signals,
                "weights_used": fusion.weights,
                "confidence_threshold": fusion.min_confidence,
                "analysis_timestamp": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Analysis complete for {symbol}: {signal_direction} (score: {final_score:.3f}, strength: {strength}%)")
        return result
        
    except Exception as e:
        logger.error(f"Critical error in generate_trade_decision for {symbol}: {e}")
        return {
            "confirmed": False,
            "signal": "ERROR",
            "avg_score": 0,
            "reason": f"Analysis failed: {str(e)}",
            "strength": 0,
            "details": {"error": str(e)}
        }

async def run_fused_analysis(symbol: str, chat_id: int = None) -> Dict:
    """
    Alternative function name for compatibility
    """
    return await generate_trade_decision(symbol, chat_id)

def get_quick_signal(symbol: str) -> str:
    """
    Quick synchronous signal for simple use cases
    """
    try:
        result = asyncio.run(generate_trade_decision(symbol))
        return result.get('signal', 'ERROR')
    except Exception as e:
        logger.error(f"Quick signal error for {symbol}: {e}")
        return "ERROR"

# Export all functions
__all__ = [
    'generate_trade_decision',
    'run_fused_analysis',
    'get_quick_signal',
    'AdvancedSignalFusion'
]