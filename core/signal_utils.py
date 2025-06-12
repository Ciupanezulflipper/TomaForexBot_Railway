# core/signal_utils.py

def calculate_signal_score(rsi_score, pattern_score, ema_score, fib_score, risk_score, weights=None):
    """
    Centralized function to calculate the total signal score using configurable weights.
    """
    if weights is None:
        weights = {
            "rsi": 1,
            "pattern": 1,
            "ema": 1,
            "fibonacci": 1,
            "risk": 1
        }

    return (
        weights['rsi'] * rsi_score +
        weights['pattern'] * pattern_score +
        weights['ema'] * ema_score +
        weights['fibonacci'] * fib_score +
        weights['risk'] * risk_score
    )


def score_bar(score: int):
    """
    Format score bar with emoji arrows.
    """
    units = min(abs(score), 5)
    block = "█" * units
    arrow = "🔺" if score > 0 else "🔻"
    return f"{block}{arrow}"
"""
Signal Processing Utilities for TomaForexBot
Helper functions for signal validation, formatting, and management
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SignalValidator:
    """Validates and sanitizes trading signals"""
    
    @staticmethod
    def validate_signal_result(result: Dict) -> Dict:
        """
        Validate and sanitize signal result structure
        """
        required_keys = ['confirmed', 'signal', 'avg_score', 'reason']
        
        # Ensure all required keys exist
        for key in required_keys:
            if key not in result:
                result[key] = None
        
        # Sanitize values
        result['confirmed'] = bool(result.get('confirmed', False))
        result['avg_score'] = float(result.get('avg_score', 0))
        result['strength'] = int(result.get('strength', 0))
        
        # Ensure signal is valid
        valid_signals = ['BUY', 'SELL', 'STRONG_BUY', 'STRONG_SELL', 'HOLD', 'ERROR', 'COOLDOWN']
        if result.get('signal') not in valid_signals:
            result['signal'] = 'ERROR'
        
        # Truncate reason if too long
        if isinstance(result.get('reason'), str) and len(result['reason']) > 500:
            result['reason'] = result['reason'][:500] + "..."
        
        return result
    
    @staticmethod
    def is_valid_symbol(symbol: str) -> bool:
        """Check if symbol format is valid"""
        if not symbol or len(symbol) < 6 or len(symbol) > 8:
            return False
        
        # Common forex pairs
        common_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURJPY', 'GBPJPY', 'EURGBP', 'AUDJPY', 'EURAUD', 'EURCHF', 'AUDNZD',
            'NZDJPY', 'GBPAUD', 'GBPCAD', 'EURNZD', 'AUDCAD', 'GBPCHF', 'CADCHF'
        ]
        
        return symbol.upper() in common_pairs

class SignalFormatter:
    """Formats signals for different output channels"""
    
    @staticmethod
    def format_for_telegram(result: Dict, symbol: str) -> str:
        """
        Format signal result for Telegram message
        """
        try:
            signal = result.get('signal', 'ERROR')
            score = result.get('avg_score', 0)
            strength = result.get('strength', 0)
            confirmed = result.get('confirmed', False)
            
            # Signal emoji mapping
            signal_emojis = {
                'STRONG_BUY': '🚀💚',
                'BUY': '📈💚',
                'STRONG_SELL': '📉❤️',
                'SELL': '📊❤️',
                'HOLD': '⏸️💛',
                'ERROR': '❌',
                'COOLDOWN': '⏰'
            }
            
            emoji = signal_emojis.get(signal, '❓')
            
            # Build message
            msg_parts = [
                f"{emoji} **{symbol}** Analysis",
                f"Signal: **{signal}**",
                f"Score: **{score:.2f}** | Strength: **{strength}%**",
                f"Confirmed: {'✅ YES' if confirmed else '❌ NO'}"
            ]
            
            # Add reason if available
            reason = result.get('reason', '')
            if reason and reason != 'No clear signals detected':
                # Truncate and clean reason for Telegram
                clean_reason = reason.replace('|', '\n•').replace(';', '\n•')
                if len(clean_reason) > 200:
                    clean_reason = clean_reason[:200] + "..."
                msg_parts.append(f"\n**Analysis:**\n• {clean_reason}")
            
            # Add timestamp
            msg_parts.append(f"\n🕐 {datetime.now().strftime('%H:%M:%S')}")
            
            return "\n".join(msg_parts)
            
        except Exception as e:
            logger.error(f"Error formatting signal for Telegram: {e}")
            return f"❌ Error formatting signal for {symbol}"
    
    @staticmethod
    def format_for_log(result: Dict, symbol: str) -> str:
        """Format signal result for plain text logs."""
        try:
            signal = result.get('signal', 'ERROR')
            score = result.get('avg_score', 0)
            strength = result.get('strength', 0)
            confirmed = result.get('confirmed', False)
            reason = result.get('reason', '')

            clean_reason = reason.replace('\n', ' ').replace('|', ';')
            if len(clean_reason) > 200:
                clean_reason = clean_reason[:200] + '...'

            status = 'YES' if confirmed else 'NO'
            timestamp = datetime.utcnow().isoformat()

            return (
                f"{timestamp} {symbol} {signal} "
                f"score={score:.2f} strength={strength}% "
                f"confirmed={status} reason={clean_reason}"
            )
        except Exception as e:
            logger.error(f"Error formatting signal for log: {e}")
            return f"Error logging signal for {symbol}"