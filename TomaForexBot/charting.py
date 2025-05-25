import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

os.makedirs('charts', exist_ok=True)

def generate_pro_chart(df, symbol, timeframe, score=None, signal_type=None, reasons=None):
    # === Type check to catch mistakes ===
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"generate_pro_chart expected DataFrame for df, got {type(df).__name__} (value: {repr(df)})")

    df = df.copy()
    df.columns = df.columns.str.lower()  # Standardize to lowercase

    # Calculate indicators if missing
    if 'ema9' not in df.columns and 'close' in df.columns:
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    if 'ema21' not in df.columns and 'close' in df.columns:
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    if 'rsi' not in df.columns and 'close' in df.columns:
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

    # Prepare title lines
    title_lines = []
    title_main = f"{symbol} - {timeframe}"
    if signal_type:
        title_main += f" - {signal_type}"
    if score is not None:
        title_main += f" (Score: {score})"
    title_lines.append(title_main)

    # Add EMA relationship to title
    if 'ema9' in df.columns and 'ema21' in df.columns:
        if df['ema9'].iloc[-1] > df['ema21'].iloc[-1]:
            title_lines.append("ema9 > ema21")
        else:
            title_lines.append("ema9 < ema21")

    # Add rsi status
    if 'rsi' in df.columns:
        rsi_val = df['rsi'].iloc[-1]
        if rsi_val > 70:
            title_lines.append("rsi overbought")
        elif rsi_val < 30:
            title_lines.append("rsi oversold")
        else:
            title_lines.append("rsi neutral")
    if reasons:
        title_lines.append(f"Reasons: {', '.join(reasons)}")

    # Plot
    fig, ax1 = plt.subplots(figsize=(10, 6))
    if 'close' in df.columns:
        ax1.plot(df.index, df['close'], color='red', linestyle='--', label='close')
    if 'ema9' in df.columns:
        ax1.plot(df.index, df['ema9'], color='orange', label='ema9')
    if 'ema21' in df.columns:
        ax1.plot(df.index, df['ema21'], color='green', label='ema21')
    ax1.set_ylabel('Price')
    ax2 = ax1.twinx()
    colors = []
    if 'close' in df.columns:
        close_vals = df['close'].values
        for i in range(1, len(close_vals)):
            colors.append('green' if close_vals[i] >= close_vals[i-1] else 'red')
        if len(close_vals) > 0:
            colors.insert(0, 'green')
    else:
        colors = ['blue'] * len(df)
    if 'volume' in df.columns:
        ax2.bar(df.index, df['volume'], color=colors, alpha=0.3, label='volume')
    ax2.set_ylabel('volume')
    ax1.legend(loc='upper left')
    plt.title("\n".join(title_lines))
    plt.tight_layout()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{timeframe}_{signal_type}_pro_{timestamp}.png"
    chart_path = os.path.join('charts', filename)
    fig.savefig(chart_path)
    plt.close(fig)
    return chart_path
