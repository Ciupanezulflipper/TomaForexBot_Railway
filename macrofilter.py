import investpy
import pandas as pd
from datetime import datetime, timedelta

# Mapping symbol to countries (extend this if needed)
SYMBOL_COUNTRY_MAP = {
    'EURUSD': ['Euro Zone', 'United States'],
    'GBPUSD': ['United Kingdom', 'United States'],
    'USDJPY': ['United States', 'Japan'],
    'AUDUSD': ['Australia', 'United States'],
    'USDCAD': ['United States', 'Canada'],
    'NZDUSD': ['New Zealand', 'United States'],
    'USDCHF': ['United States', 'Switzerland'],
    'XAUUSD': ['United States'],
    'XAGUSD': ['United States'],
    'US30': ['United States'],
    'NAS100': ['United States'],
    'SPX500': ['United States'],
    'DAX40': ['Germany'],
    'GBPJPY': ['United Kingdom', 'Japan'],
    'EURGBP': ['Euro Zone', 'United Kingdom'],
    'BTCUSD': ['United States'],
    'ETHUSD': ['United States'],
}

def get_relevant_countries(symbol: str):
    symbol = symbol.upper()
    return SYMBOL_COUNTRY_MAP.get(symbol, [])

def get_upcoming_high_impact_events():
    try:
        df = investpy.news.economic_calendar(time_zone='GMT', time_filter='time_remaining', countries=[], importances=['high'])
        df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'])
        df = df[df['datetime'] >= datetime.utcnow()]
        return df
    except Exception as e:
        print(f"[MacroFilter] Failed to fetch economic calendar: {e}")
        return pd.DataFrame()

def check_macro_filter(symbol: str, window_minutes: int = 15):
    now = datetime.utcnow()
    countries = get_relevant_countries(symbol)
    if not countries:
        return {"block": False, "note": "⚠️ Unknown country map"}

    events = get_upcoming_high_impact_events()
    if events.empty:
        return {"block": False, "note": "✅ None"}

    filtered = events[events['country'].isin(countries)]
    for _, row in filtered.iterrows():
        event_time = row['datetime']
        delta = (event_time - now).total_seconds() / 60
        if -window_minutes <= delta <= window_minutes:
            name = row['event']
            note = f"⚠️ {name} in {int(delta)}min"
            return {"block": True, "note": note}

    return {"block": False, "note": "✅ None"}
