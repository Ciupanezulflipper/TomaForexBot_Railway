import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Ensure the charts directory exists
os.makedirs('charts', exist_ok=True)

def generate_basic_chart(symbol, timeframe, data, signal_type=None, score=None):
    """
    Generate and save a basic price chart.
    """
    # Copy data to avoid modifying original
    df = data.copy()
    
    # Ensure datetime index
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        for col in ['Date', 'date', 'Datetime', 'datetime', 'time', 'Time']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                df.set_index(col, inplace=True)
                break
        else:
            df.index = pd.to_datetime(df.index, errors='ignore')
    
    # Prepare chart title lines
    title_lines = []
    title_main = f"{symbol} - {timeframe}"
    if signal_type:
        title_main += f" - {signal_type}"
    if score is not None:
        title_main += f" (Score: {score})"
    title_lines.append(title_main)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    # Plot the closing price line (or last column if 'Close' not present)
    if 'Close' in df.columns:
        ax.plot(df.index, df['Close'], color='orange', label='Close')
    else:
        ax.plot(df.index, df.iloc[:, -1], color='orange', label='Price')
    # Add error bars for confidence band (green lines)
    if 'Close' in df.columns:
        err = df['Close'] * 0.002  # e.g., 0.2% error
        ax.errorbar(df.index, df['Close'], yerr=err, fmt='none', ecolor='green', alpha=0.5)
    # Rotate x-axis labels for readability
    ax.tick_params(axis='x', rotation=45)
    # Label the price axis (on the right side)
    ax.set_ylabel('Price')
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    
    # Set the chart title
    title_text = "\n".join(title_lines)
    plt.title(title_text)
    
    plt.tight_layout()
    # Save the chart image with a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{timeframe}_basic_{timestamp}.png"
    chart_path = os.path.join('charts', filename)
    fig.savefig(chart_path)
    plt.close(fig)
    return chart_path

def generate_pro_chart(symbol, timeframe, data, signal_type=None, score=None):
    """
    Generate and save an advanced chart with EMAs and volume.
    """
    # Copy data to avoid modifying original
    df = data.copy()
    
    # Ensure datetime index
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        for col in ['Date', 'date', 'Datetime', 'datetime', 'time', 'Time']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                df.set_index(col, inplace=True)
                break
        else:
            df.index = pd.to_datetime(df.index, errors='ignore')
    
    # Ensure volume column is named 'Volume'
    if 'volume' in df.columns:
        df.rename(columns={'volume': 'Volume'}, inplace=True)
    if 'Volume' not in df.columns:
        df['Volume'] = 0  # Create dummy if missing
    
    # Calculate EMA indicators
    if 'Close' in df.columns:
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # Calculate RSI (14-period)
    if 'Close' in df.columns:
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
    
    # Prepare chart title lines
    title_lines = []
    title_main = f"{symbol} - {timeframe}"
    if signal_type:
        title_main += f" - {signal_type}"
    if score is not None:
        title_main += f" (Score: {score})"
    title_lines.append(title_main)
    # Add EMA relationship to title
    if 'EMA9' in df.columns and 'EMA21' in df.columns:
        if df['EMA9'].iloc[-1] > df['EMA21'].iloc[-1]:
            title_lines.append("EMA9 > EMA21")
        else:
            title_lines.append("EMA9 < EMA21")
    # Add RSI status to title
    if 'RSI' in df.columns:
        rsi_val = df['RSI'].iloc[-1]
        if rsi_val > 70:
            title_lines.append("RSI overbought")
        elif rsi_val < 30:
            title_lines.append("RSI oversold")
        else:
            title_lines.append("RSI neutral")
    
    # Create the plot
    fig, ax1 = plt.subplots(figsize=(10, 6))
    # Plot price and EMA lines
    if 'Close' in df.columns:
        ax1.plot(df.index, df['Close'], color='red', linestyle='--', label='Close')
    if 'EMA9' in df.columns:
        ax1.plot(df.index, df['EMA9'], color='orange', label='EMA9')
    if 'EMA21' in df.columns:
        ax1.plot(df.index, df['EMA21'], color='green', label='EMA21')
    ax1.set_ylabel('Price')
    # Create a second axis for volume
    ax2 = ax1.twinx()
    # Determine bar colors: green if price went up, red if down
    colors = []
    if 'Close' in df.columns:
        close_vals = df['Close'].values
        for i in range(1, len(close_vals)):
            colors.append('green' if close_vals[i] >= close_vals[i-1] else 'red')
        if len(close_vals) > 0:
            colors.insert(0, 'green')
    else:
        colors = ['blue'] * len(df)
    ax2.bar(df.index, df['Volume'], color=colors, alpha=0.3, label='Volume')
    ax2.set_ylabel('Volume')
    # Add legend for price and EMAs
    ax1.legend(loc='upper left')
    
    # Set the chart title
    title_text = "\n".join(title_lines)
    plt.title(title_text)
    
    plt.tight_layout()
    # Save the chart image with a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{timeframe}_{signal_type}_pro_{timestamp}.png"
    chart_path = os.path.join('charts', filename)
    fig.savefig(chart_path)
    plt.close(fig)
    return chart_path
