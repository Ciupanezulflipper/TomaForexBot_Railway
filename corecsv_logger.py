import csv
import os
from datetime import datetime

def log_to_csv(filename: str, data: dict, fieldnames: list):
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(data)

def log_news_alert(article: dict):
    filename = "logs/news_alerts.csv"
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "title": article.get("title", ""),
        "source": article.get("source", {}).get("name", ""),
        "publishedAt": article.get("publishedAt", ""),
        "url": article.get("url", "")
    }
    fieldnames = ["timestamp", "title", "source", "publishedAt", "url"]
    log_to_csv(filename, data, fieldnames)

def log_trade_signal(signal: dict):
    filename = "logs/trade_signals.csv"
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "pair": signal["pair"],
        "bias": signal["bias"],
        "score": signal["score"],
        "entry": signal["entry"],
        "sl": signal["sl"],
        "tp": signal["tp"],
        "rr": signal["r_r"],
        "confidence": signal["confidence"]
    }
    fieldnames = ["timestamp", "pair", "bias", "score", "entry", "sl", "tp", "rr", "confidence"]
    log_to_csv(filename, data, fieldnames)
