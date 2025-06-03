import os
from dotenv import load_dotenv
import datetime
from news_feeds import fetch_rss_headlines, fetch_reddit_headlines
from news_signal_logic import analyze_news_headline, send_telegram_message

load_dotenv()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

def fetch_today_headlines():
    # Collect today's headlines from RSS and Reddit
    headlines = []
    today = datetime.datetime.utcnow().date()
    for published, title, link in fetch_rss_headlines() + fetch_reddit_headlines():
        # Try to parse published date
        try:
            pub_date = None
            if isinstance(published, str) and published:
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M"]:
                    try:
                        pub_date = datetime.datetime.strptime(published[:len(fmt)], fmt).date()
                        break
                    except Exception:
                        continue
            if pub_date is None:
                pub_date = today  # fallback, just in case
        except Exception:
            pub_date = today
        if pub_date == today:
            headlines.append((title, link))
    return headlines

def is_actionable_signal(signals):
    # Returns True if at least one signal is BUY/SELL (not HOLD)
    for signal in signals:
        if signal.get('signal', '').upper() in ['BUY', 'SELL']:
            return True
    return False

def main():
    headlines = fetch_today_headlines()
    sent = 0
    for title, link in headlines:
        signals = analyze_news_headline(title)
        if is_actionable_signal(signals):
            # Build and send alert message
            msg_lines = [f"📰 Headline: {title}\n{link}"]
            for s in signals:
                if s.get('signal', '').upper() in ['BUY', 'SELL']:
                    msg_lines.append(f"- {s['asset']}: {s['signal']} ({s['reason']})")
            msg = "\n".join(msg_lines)
            # Send to Telegram
            try:
                send_telegram_message(msg, TELEGRAM_CHAT_ID)
                sent += 1
            except Exception as e:
                print(f"[Telegram ERROR] {e}")
    print(f"Checked {len(headlines)} headlines. Sent {sent} actionable alerts.")

if __name__ == "__main__":
    main()
    print("Manual news auto-send check complete.")
