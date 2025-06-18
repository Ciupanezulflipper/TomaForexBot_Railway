"""Utility indicator calculations with logging and extra indicators."""

from __future__ import annotations
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_ema(series: pd.Series, period: int = 9) -> pd.Series:
    """Exponential Moving Average."""
    logger.debug(f"Calculating EMA: {series.name}, len={len(series)}, period={period}")
    return series.ewm(span=period, adjust=False).mean()

def calculate_sma(series: pd.Series, period: int = 9) -> pd.Series:
    """Simple Moving Average."""
    logger.debug(f"Calculating SMA: {series.name}, len={len(series)}, period={period}")
    return series.rolling(window=period).mean()

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(to_replace=0, method="ffill")
    rsi = 100 - (100 / (1 + rs))
    logger.debug(f"RSI calculated: period={period}")
    return rsi

def calculate_macd(series: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """MACD, Signal, Histogram."""
    ema_fast = calculate_ema(series, fast_period)
    ema_slow = calculate_ema(series, slow_period)
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal
    logger.debug(f"MACD calculated: fast={fast_period}, slow={slow_period}, signal={signal_period}")
    return pd.DataFrame({'macd': macd, 'signal': signal, 'histogram': histogram})

def calculate_bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands: Middle, Upper, Lower."""
    middle_band = calculate_sma(series, period)
    std = series.rolling(window=period).std()
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    logger.debug(f"Bollinger Bands calculated: period={period}, num_std={num_std}")
    return pd.DataFrame({"middle_band": middle_band, "upper_band": upper_band, "lower_band": lower_band})

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range."""
    high_low = high - low
    high_close = (high - close.shift()).abs()
    low_close = (low - close.shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    logger.debug(f"ATR calculated: period={period}")
    return atr

def calculate_stochastic_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator (%K, %D)."""
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    percent_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    percent_d = percent_k.rolling(window=d_period).mean()
    logger.debug(f"Stochastic Oscillator calculated: k_period={k_period}, d_period={d_period}")
    return pd.DataFrame({'%K': percent_k, '%D': percent_d})

def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """Commodity Channel Index."""
    tp = (high + low + close) / 3
    sma = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: pd.Series(x).mad(), raw=False)
    cci = (tp - sma) / (0.015 * mad)
    logger.debug(f"CCI calculated: period={period}")
    return cci

def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Williams %R."""
    highest_high = high.rolling(window=period).max()
    lowest_low = low.rolling(window=period).min()
    williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
    logger.debug(f"Williams %R calculated: period={period}")
    return williams_r

# --- Example signal generation functions ---

def rsi_signal(rsi_series: pd.Series, oversold: int = 30, overbought: int = 70) -> pd.Series:
    """RSI Buy/Sell: Buy if RSI < oversold, Sell if RSI > overbought."""
    signals = pd.Series(index=rsi_series.index, dtype="object")
    signals[rsi_series < oversold] = "BUY"
    signals[rsi_series > overbought] = "SELL"
    logger.debug("RSI signals generated.")
    return signals

def macd_signal(macd_df: pd.DataFrame) -> pd.Series:
    """MACD Buy/Sell: Buy if MACD crosses above Signal, Sell if MACD crosses below."""
    signals = pd.Series(index=macd_df.index, dtype="object")
    macd = macd_df['macd']
    signal = macd_df['signal']
    cross_up = (macd > signal) & (macd.shift() <= signal.shift())
    cross_down = (macd < signal) & (macd.shift() >= signal.shift())
    signals[cross_up] = "BUY"
    signals[cross_down] = "SELL"
    logger.debug("MACD signals generated.")
    return signals

def bollinger_signal(close: pd.Series, bb_df: pd.DataFrame) -> pd.Series:
    """Bollinger Bands Buy/Sell: Buy if close < lower_band, Sell if close > upper_band."""
    signals = pd.Series(index=close.index, dtype="object")
    signals[close < bb_df['lower_band']] = "BUY"
    signals[close > bb_df['upper_band']] = "SELL"
    logger.debug("Bollinger Bands signals generated.")
    return signals

def stochastic_signal(stoch_df: pd.DataFrame, oversold: int = 20, overbought: int = 80) -> pd.Series:
    """Stochastic Oscillator Buy/Sell: Buy if %K < oversold, Sell if %K > overbought."""
    signals = pd.Series(index=stoch_df.index, dtype="object")
    signals[stoch_df['%K'] < oversold] = "BUY"
    signals[stoch_df['%K'] > overbought] = "SELL"
    logger.debug("Stochastic Oscillator signals generated.")
    return signals

def cci_signal(cci_series: pd.Series, oversold: int = -100, overbought: int = 100) -> pd.Series:
    """CCI Buy/Sell: Buy if CCI < oversold, Sell if CCI > overbought."""
    signals = pd.Series(index=cci_series.index, dtype="object")
    signals[cci_series < oversold] = "BUY"
    signals[cci_series > overbought] = "SELL"
    logger.debug("CCI signals generated.")
    return signals

def williams_r_signal(wr_series: pd.Series, oversold: int = -80, overbought: int = -20) -> pd.Series:
    """Williams %R Buy/Sell: Buy if %R < oversold, Sell if %R > overbought."""
    signals = pd.Series(index=wr_series.index, dtype="object")
    signals[wr_series < oversold] = "BUY"
    signals[wr_series > overbought] = "SELL"
    logger.debug("Williams %R signals generated.")
    return signals

# --- Example usage/test ---

def example_usage(df: pd.DataFrame):
    """
    Example usage for generating BUY/SELL signals.
    df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
    """
    close = df['close']
    high = df['high']
    low = df['low']

    rsi = calculate_rsi(close)
    rsi_signals = rsi_signal(rsi)

    macd_df = calculate_macd(close)
    macd_signals = macd_signal(macd_df)

    bb_df = calculate_bollinger_bands(close)
    bb_signals = bollinger_signal(close, bb_df)

    stoch_df = calculate_stochastic_oscillator(high, low, close)
    stoch_signals = stochastic_signal(stoch_df)

    cci = calculate_cci(high, low, close)
    cci_signals = cci_signal(cci)

    wr = calculate_williams_r(high, low, close)
    wr_signals = williams_r_signal(wr)

    logger.info("Example signals generated (last 5 rows):")
    print("RSI signals:\n", rsi_signals.dropna().tail())
    print("MACD signals:\n", macd_signals.dropna().tail())
    print("Bollinger Band signals:\n", bb_signals.dropna().tail())
    print("Stochastic signals:\n", stoch_signals.dropna().tail())
    print("CCI signals:\n", cci_signals.dropna().tail())
    print("Williams %R signals:\n", wr_signals.dropna().tail())