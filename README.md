# TomaForexBot – Free Modular Forex Assistant

This bot scans the market using technical indicators, news events, and sentiment signals, then alerts you via Telegram.

---

## 🧠 Features

- Modular file structure
- Fully async & testable
- Free APIs: NewsAPI + ExchangeRate-API
- Alerts when news matches technical setups
- Commands like `/scan EURUSD`, `/signal`, `/summary`
- Logging to CSV
- Customizable strategy scoring

---

## 🚀 Getting Started

1. **Clone the repo and install dependencies**

```bash
git clone https://github.com/YourUsername/TomaForexBot.git
cd TomaForexBot
pip install -r requirements.txt
```

## 🧪 Running Tests

Install dependencies before running tests:

```bash
pip install -r requirements.txt
```

If Finnhub tests run without monkeypatching API calls, set the
`FINNHUB_API_KEY` environment variable. Network connectivity is required unless
requests are mocked.

Optional packages (for example `MetaTrader5`) may not be available in some
environments such as CI. The project does not rely on `MetaTrader5` because
there is no free API, so related tests should be disabled or mocked if the
package is missing.