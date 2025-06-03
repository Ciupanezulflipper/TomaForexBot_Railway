import os
import csv

CSV_FILE = "trade_signals.csv"

def log_to_csv(signal_data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=signal_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(signal_data)
