+import pandas as pd
+import aiohttp
+import asyncio
+from typing import Optional, Dict, Any
+import logging
+from datetime import datetime, timedelta
+import os
+
+logger = logging.getLogger(__name__)
+import pandas as pd
import aiohttp
import asyncio
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class CloudBotDataIntegration:
    """Corrected data integration methods for different forex data providers"""

    def __init__(self):
        # Get API keys from environment variables for security
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.oanda_api_key = os.getenv("OANDA_API_KEY", "")
        self.oanda_account_id = os.getenv("OANDA_ACCOUNT_ID", "")
        self.fxpro_api_key = os.getenv("FXPRO_API_KEY", "")

    # METHOD 1: Alpha Vantage Integration (CORRECTED)
    async def _get_ohlc_data_alpha_vantage(
        self, pair: str, timeframe: str = "1H", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLC data from Alpha Vantage API (FREE TIER: 25 requests/day)"""
        try:
            if not self.alpha_vantage_key:
                logger.error("Alpha Vantage API key not configured")
                return None

            from_symbol = pair[:3]
            to_symbol = pair[3:]

            interval_map = {
                "1M": "1min",
                "5M": "5min",
                "15M": "15min",
                "30M": "30min",
                "1H": "60min",
            }

            if timeframe in interval_map:
                function = "FX_INTRADAY"
                interval = interval_map[timeframe]
                params = {
                    "function": function,
                    "from_symbol": from_symbol,
                    "to_symbol": to_symbol,
                    "interval": interval,
                    "apikey": self.alpha_vantage_key,
                    "outputsize": "full" if limit > 100 else "compact",
                }
            else:
                function = "FX_DAILY"
                params = {
                    "function": function,
                    "from_symbol": from_symbol,
                    "to_symbol": to_symbol,
                    "apikey": self.alpha_vantage_key,
                    "outputsize": "full" if limit > 100 else "compact",
                }

            url = "https://www.alphavantage.co/query"

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(
                            "Alpha Vantage API HTTP error: %s", response.status
                        )
                        return None
                    data = await response.json()

                    if "Error Message" in data:
                        logger.error(
                            "Alpha Vantage API error: %s", data["Error Message"]
                        )
                        return None
                    if "Note" in data:
                        logger.warning(
                            "Alpha Vantage rate limit: %s", data["Note"]
                        )
                        return None

                    time_series = None
                    for key in data.keys():
                        if "Time Series" in key:
                            time_series = data[key]
                            break
                    if not time_series:
                        logger.error("No time series data found for %s", pair)
                        return None

                    df_data = []
                    for timestamp, ohlc in time_series.items():
                        try:
                            df_data.append(
                                {
                                    "timestamp": pd.to_datetime(timestamp),
                                    "Open": float(ohlc["1. open"]),
                                    "High": float(ohlc["2. high"]),
                                    "Low": float(ohlc["3. low"]),
                                    "Close": float(ohlc["4. close"]),
                                }
                            )
                        except (KeyError, ValueError) as exc:
                            logger.warning("Skipping invalid data point: %s", exc)
                            continue

                    if not df_data:
                        logger.error("No valid data points for %s", pair)
                        return None

                    df = pd.DataFrame(df_data)
                    df.set_index("timestamp", inplace=True)
                    df.sort_index(inplace=True)
                    if len(df) > limit:
                        df = df.tail(limit)

                    logger.info(
                        "✅ Fetched %s candles for %s from Alpha Vantage",
                        len(df),
                        pair,
                    )
                    return df

        except asyncio.TimeoutError:
            logger.error("Timeout fetching Alpha Vantage data for %s", pair)
            return None
        except Exception as exc:
            logger.error("Error fetching Alpha Vantage data for %s: %s", pair, exc)
            return None

    # METHOD 2: OANDA Integration (CORRECTED)
    async def _get_ohlc_data_oanda(
        self, pair: str, timeframe: str = "1H", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLC data from OANDA API (Requires live account)"""
        try:
            if not self.oanda_api_key:
                logger.error("OANDA API key not configured")
                return None

            oanda_instrument = f"{pair[:3]}_{pair[3:]}"
            granularity_map = {
                "1M": "M1",
                "5M": "M5",
                "15M": "M15",
                "30M": "M30",
                "1H": "H1",
                "4H": "H4",
                "1D": "D",
            }
            granularity = granularity_map.get(timeframe, "H1")

            base_url = "https://api-fxpractice.oanda.com"
            url = f"{base_url}/v3/instruments/{oanda_instrument}/candles"
            headers = {
                "Authorization": f"Bearer {self.oanda_api_key}",
                "Content-Type": "application/json",
            }
            params = {
                "granularity": granularity,
                "count": min(limit, 500),
                "price": "M",
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 401:
                        logger.error("OANDA authentication failed - check API key")
                        return None
                    if response.status == 404:
                        logger.error(
                            "OANDA instrument not found: %s", oanda_instrument
                        )
                        return None
                    if response.status != 200:
                        logger.error("OANDA API error: %s", response.status)
                        return None
                    data = await response.json()

                    if "candles" not in data or not data["candles"]:
                        logger.error(
                            "No candles data in OANDA response for %s", pair
                        )
                        return None

                    df_data = []
                    for candle in data["candles"]:
                        if candle.get("complete", False):
                            try:
                                mid_data = candle.get("mid", {})
                                df_data.append(
                                    {
                                        "timestamp": pd.to_datetime(candle["time"]),
                                        "Open": float(mid_data["o"]),
                                        "High": float(mid_data["h"]),
                                        "Low": float(mid_data["l"]),
                                        "Close": float(mid_data["c"]),
                                    }
                                )
                            except (KeyError, ValueError) as exc:
                                logger.warning(
                                    "Skipping invalid OANDA candle: %s", exc
                                )
                                continue

                    if not df_data:
                        logger.error("No valid candles for %s", pair)
                        return None

                    df = pd.DataFrame(df_data)
                    df.set_index("timestamp", inplace=True)
                    df.sort_index(inplace=True)

                    logger.info(
                        "✅ Fetched %s candles for %s from OANDA", len(df), pair
                    )
                    return df
        except Exception as exc:
            logger.error("Error fetching OANDA data for %s: %s", pair, exc)
            return None

    # METHOD 3: Free Forex API (CORRECTED - New Alternative)
    async def _get_ohlc_data_fxpro(
        self, pair: str, timeframe: str = "1H", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLC data from FXPro or similar free API"""
        try:
            timeframe_map = {
                "1M": "1",
                "5M": "5",
                "15M": "15",
                "30M": "30",
                "1H": "60",
                "4H": "240",
                "1D": "1440",
            }
            interval = timeframe_map.get(timeframe, "60")

            url = "https://api.fxpricing.com/v1/prices"
            params = {"instrument": pair, "period": interval, "count": limit}

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error("Free API error: %s", response.status)
                        return None
                    data = await response.json()

                    df_data = []
                    for item in data.get("prices", []):
                        try:
                            df_data.append(
                                {
                                    "timestamp": pd.to_datetime(item["time"]),
                                    "Open": float(item["open"]),
                                    "High": float(item["high"]),
                                    "Low": float(item["low"]),
                                    "Close": float(item["close"]),
                                }
                            )
                        except (KeyError, ValueError):
                            continue

                    if not df_data:
                        return None

                    df = pd.DataFrame(df_data)
                    df.set_index("timestamp", inplace=True)
                    df.sort_index(inplace=True)

                    logger.info(
                        "✅ Fetched %s candles for %s from Free API", len(df), pair
                    )
                    return df
        except Exception as exc:
            logger.error("Error fetching free API data for %s: %s", pair, exc)
            return None

    # METHOD 4: Fallback Mock Data (FOR TESTING)
    async def _get_ohlc_data_mock(
        self, pair: str, timeframe: str = "1H", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Generate mock OHLC data for testing purposes"""
        try:
            import numpy as np

            np.random.seed(42)
            base_prices = {
                "EURUSD": 1.0800,
                "GBPUSD": 1.2500,
                "USDJPY": 150.00,
                "AUDUSD": 0.6500,
                "USDCAD": 1.3500,
                "USDCHF": 0.9000,
                "NZDUSD": 0.6000,
            }
            base_price = base_prices.get(pair, 1.0000)

            end_time = datetime.now()
            if timeframe == "1M":
                freq = "1T"
            elif timeframe == "5M":
                freq = "5T"
            elif timeframe == "15M":
                freq = "15T"
            elif timeframe == "30M":
                freq = "30T"
            elif timeframe == "1H":
                freq = "1H"
            elif timeframe == "4H":
                freq = "4H"
            else:
                freq = "1D"

            timestamps = pd.date_range(end=end_time, periods=limit, freq=freq)

            df_data = []
            current_price = base_price
            for timestamp in timestamps:
                price_change = np.random.normal(0, 0.001) * current_price
                open_price = current_price
                close_price = current_price + price_change
                high_price = max(open_price, close_price) + abs(
                    np.random.normal(0, 0.0005)
                ) * current_price
                low_price = min(open_price, close_price) - abs(
                    np.random.normal(0, 0.0005)
                ) * current_price
                df_data.append(
                    {
                        "timestamp": timestamp,
                        "Open": round(open_price, 5),
                        "High": round(high_price, 5),
                        "Low": round(low_price, 5),
                        "Close": round(close_price, 5),
                    }
                )
                current_price = close_price

            df = pd.DataFrame(df_data)
            df.set_index("timestamp", inplace=True)
            logger.info("✅ Generated %s mock candles for %s", len(df), pair)
            return df
        except Exception as exc:
            logger.error("Error generating mock data for %s: %s", pair, exc)
            return None

    # METHOD 5: Yahoo Finance (FREE ALTERNATIVE)
    async def _get_ohlc_data_yahoo(
        self, pair: str, timeframe: str = "1H", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLC data from Yahoo Finance (Free but limited forex pairs)"""
        try:
            yahoo_symbol = f"{pair}=X"
            interval_map = {
                "1M": "1m",
                "5M": "5m",
                "15M": "15m",
                "30M": "30m",
                "1H": "1h",
                "1D": "1d",
            }
            interval = interval_map.get(timeframe, "1h")

            if timeframe in ["1M", "5M"]:
                period = "7d"
            elif timeframe in ["15M", "30M", "1H"]:
                period = "60d"
            else:
                period = "1y"

            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            params = {
                "interval": interval,
                "period1": int((datetime.now() - timedelta(days=30)).timestamp()),
                "period2": int(datetime.now().timestamp()),
                "includePrePost": "false",
            }

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error("Yahoo Finance API error: %s", response.status)
                        return None
                    data = await response.json()

                    if "chart" not in data or not data["chart"]["result"]:
                        logger.error("No chart data from Yahoo Finance for %s", pair)
                        return None
                    result = data["chart"]["result"][0]
                    timestamps = result["timestamp"]
                    ohlc_data = result["indicators"]["quote"][0]

                    df_data = []
                    for i, ts in enumerate(timestamps):
                        try:
                            df_data.append(
                                {
                                    "timestamp": pd.to_datetime(ts, unit="s"),
                                    "Open": float(ohlc_data["open"][i]),
                                    "High": float(ohlc_data["high"][i]),
                                    "Low": float(ohlc_data["low"][i]),
                                    "Close": float(ohlc_data["close"][i]),
                                }
                            )
                        except (TypeError, ValueError, IndexError):
                            continue

                    if not df_data:
                        logger.error("No valid data from Yahoo Finance for %s", pair)
                        return None

                    df = pd.DataFrame(df_data)
                    df.set_index("timestamp", inplace=True)
                    df.sort_index(inplace=True)
                    if len(df) > limit:
                        df = df.tail(limit)

                    logger.info(
                        "✅ Fetched %s candles for %s from Yahoo Finance",
                        len(df),
                        pair,
                    )
                    return df
        except Exception as exc:
            logger.error("Error fetching Yahoo Finance data for %s: %s", pair, exc)
            return None

    # MAIN METHOD - Choose your data source
    async def _get_ohlc_data(
        self, pair: str, timeframe: str = "1H", limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Main data fetching method with fallback strategy"""
        methods = [
            # ("Yahoo Finance", self._get_ohlc_data_yahoo),
            # ("Alpha Vantage", self._get_ohlc_data_alpha_vantage),
            # ("OANDA", self._get_ohlc_data_oanda),
            ("Mock Data", self._get_ohlc_data_mock),
        ]

        for method_name, method_func in methods:
            try:
                logger.info("Trying %s for %s", method_name, pair)
                df = await method_func(pair, timeframe, limit)
                if df is not None and not df.empty:
                    logger.info(
                        "✅ Successfully fetched data using %s", method_name
                    )
                    return df
                logger.warning(
                    "❌ %s returned empty data for %s", method_name, pair
                )
            except Exception as exc:
                logger.error("❌ %s failed for %s: %s", method_name, pair, exc)
                continue

        logger.error("❌ All data sources failed for %s", pair)
        return None


"""Integration instructions for your CloudBot class:

1. Add this to your CloudBot __init__ method:
   self.data_integration = CloudBotDataIntegration()

2. Replace your _get_ohlc_data method with:
   async def _get_ohlc_data(self, pair: str, timeframe: str = '1H', limit: int = 100):
       return await self.data_integration._get_ohlc_data(pair, timeframe, limit)

3. Set environment variables for API keys:
   export ALPHA_VANTAGE_API_KEY="your_key_here"
   export OANDA_API_KEY="your_key_here"
   export OANDA_ACCOUNT_ID="your_account_id"

4. Install required packages:
   pip install aiohttp pandas numpy

5. Choose your preferred data source by editing the methods list in _get_ohlc_data()
"""
+
+class CloudBotDataIntegration:
+    """Corrected data integration methods for different forex data providers"""
+
+    def __init__(self):
+        # Get API keys from environment variables for security
+        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
+        self.oanda_api_key = os.getenv("OANDA_API_KEY", "")
+        self.oanda_account_id = os.getenv("OANDA_ACCOUNT_ID", "")
+        self.fxpro_api_key = os.getenv("FXPRO_API_KEY", "")
+
+    # METHOD 1: Alpha Vantage Integration (CORRECTED)
+    async def _get_ohlc_data_alpha_vantage(
+        self, pair: str, timeframe: str = "1H", limit: int = 100
+    ) -> Optional[pd.DataFrame]:
+        """Fetch OHLC data from Alpha Vantage API (FREE TIER: 25 requests/day)"""
+        try:
+            if not self.alpha_vantage_key:
+                logger.error("Alpha Vantage API key not configured")
+                return None
+
+            from_symbol = pair[:3]
+            to_symbol = pair[3:]
+
+            interval_map = {
+                "1M": "1min",
+                "5M": "5min",
+                "15M": "15min",
+                "30M": "30min",
+                "1H": "60min",
+            }
+
+            if timeframe in interval_map:
+                function = "FX_INTRADAY"
+                interval = interval_map[timeframe]
+                params = {
+                    "function": function,
+                    "from_symbol": from_symbol,
+                    "to_symbol": to_symbol,
+                    "interval": interval,
+                    "apikey": self.alpha_vantage_key,
+                    "outputsize": "full" if limit > 100 else "compact",
+                }
+            else:
+                function = "FX_DAILY"
+                params = {
+                    "function": function,
+                    "from_symbol": from_symbol,
+                    "to_symbol": to_symbol,
+                    "apikey": self.alpha_vantage_key,
+                    "outputsize": "full" if limit > 100 else "compact",
+                }
+
+            url = "https://www.alphavantage.co/query"
+
+            async with aiohttp.ClientSession(
+                timeout=aiohttp.ClientTimeout(total=30)
+            ) as session:
+                async with session.get(url, params=params) as response:
+                    if response.status != 200:
+                        logger.error(
+                            "Alpha Vantage API HTTP error: %s", response.status
+                        )
+                        return None
+                    data = await response.json()
+
+                    if "Error Message" in data:
+                        logger.error(
+                            "Alpha Vantage API error: %s", data["Error Message"]
+                        )
+                        return None
+                    if "Note" in data:
+                        logger.warning(
+                            "Alpha Vantage rate limit: %s", data["Note"]
+                        )
+                        return None
+
+                    time_series = None
+                    for key in data.keys():
+                        if "Time Series" in key:
+                            time_series = data[key]
+                            break
+                    if not time_series:
+                        logger.error("No time series data found for %s", pair)
+                        return None
+
+                    df_data = []
+                    for timestamp, ohlc in time_series.items():
+                        try:
+                            df_data.append(
+                                {
+                                    "timestamp": pd.to_datetime(timestamp),
+                                    "Open": float(ohlc["1. open"]),
+                                    "High": float(ohlc["2. high"]),
+                                    "Low": float(ohlc["3. low"]),
+                                    "Close": float(ohlc["4. close"]),
+                                }
+                            )
+                        except (KeyError, ValueError) as exc:
+                            logger.warning("Skipping invalid data point: %s", exc)
+                            continue
+
+                    if not df_data:
+                        logger.error("No valid data points for %s", pair)
+                        return None
+
+                    df = pd.DataFrame(df_data)
+                    df.set_index("timestamp", inplace=True)
+                    df.sort_index(inplace=True)
+                    if len(df) > limit:
+                        df = df.tail(limit)
+
+                    logger.info(
+                        "✅ Fetched %s candles for %s from Alpha Vantage",
+                        len(df),
+                        pair,
+                    )
+                    return df
+
+        except asyncio.TimeoutError:
+            logger.error("Timeout fetching Alpha Vantage data for %s", pair)
+            return None
+        except Exception as exc:
+            logger.error("Error fetching Alpha Vantage data for %s: %s", pair, exc)
+            return None
+
+    # METHOD 2: OANDA Integration (CORRECTED)
+    async def _get_ohlc_data_oanda(
+        self, pair: str, timeframe: str = "1H", limit: int = 100
+    ) -> Optional[pd.DataFrame]:
+        """Fetch OHLC data from OANDA API (Requires live account)"""
+        try:
+            if not self.oanda_api_key:
+                logger.error("OANDA API key not configured")
+                return None
+
+            oanda_instrument = f"{pair[:3]}_{pair[3:]}"
+            granularity_map = {
+                "1M": "M1",
+                "5M": "M5",
+                "15M": "M15",
+                "30M": "M30",
+                "1H": "H1",
+                "4H": "H4",
+                "1D": "D",
+            }
+            granularity = granularity_map.get(timeframe, "H1")
+
+            base_url = "https://api-fxpractice.oanda.com"
+            url = f"{base_url}/v3/instruments/{oanda_instrument}/candles"
+            headers = {
+                "Authorization": f"Bearer {self.oanda_api_key}",
+                "Content-Type": "application/json",
+            }
+            params = {
+                "granularity": granularity,
+                "count": min(limit, 500),
+                "price": "M",
+            }
+
+            async with aiohttp.ClientSession(
+                timeout=aiohttp.ClientTimeout(total=30)
+            ) as session:
+                async with session.get(url, headers=headers, params=params) as response:
+                    if response.status == 401:
+                        logger.error("OANDA authentication failed - check API key")
+                        return None
+                    if response.status == 404:
+                        logger.error(
+                            "OANDA instrument not found: %s", oanda_instrument
+                        )
+                        return None
+                    if response.status != 200:
+                        logger.error("OANDA API error: %s", response.status)
+                        return None
+                    data = await response.json()
+
+                    if "candles" not in data or not data["candles"]:
+                        logger.error(
+                            "No candles data in OANDA response for %s", pair
+                        )
+                        return None
+
+                    df_data = []
+                    for candle in data["candles"]:
+                        if candle.get("complete", False):
+                            try:
+                                mid_data = candle.get("mid", {})
+                                df_data.append(
+                                    {
+                                        "timestamp": pd.to_datetime(candle["time"]),
+                                        "Open": float(mid_data["o"]),
+                                        "High": float(mid_data["h"]),
+                                        "Low": float(mid_data["l"]),
+                                        "Close": float(mid_data["c"]),
+                                    }
+                                )
+                            except (KeyError, ValueError) as exc:
+                                logger.warning(
+                                    "Skipping invalid OANDA candle: %s", exc
+                                )
+                                continue
+
+                    if not df_data:
+                        logger.error("No valid candles for %s", pair)
+                        return None
+
+                    df = pd.DataFrame(df_data)
+                    df.set_index("timestamp", inplace=True)
+                    df.sort_index(inplace=True)
+
+                    logger.info(
+                        "✅ Fetched %s candles for %s from OANDA", len(df), pair
+                    )
+                    return df
+        except Exception as exc:
+            logger.error("Error fetching OANDA data for %s: %s", pair, exc)
+            return None
+
+    # METHOD 3: Free Forex API (CORRECTED - New Alternative)
+    async def _get_ohlc_data_fxpro(
+        self, pair: str, timeframe: str = "1H", limit: int = 100
+    ) -> Optional[pd.DataFrame]:
+        """Fetch OHLC data from FXPro or similar free API"""
+        try:
+            timeframe_map = {
+                "1M": "1",
+                "5M": "5",
+                "15M": "15",
+                "30M": "30",
+                "1H": "60",
+                "4H": "240",
+                "1D": "1440",
+            }
+            interval = timeframe_map.get(timeframe, "60")
+
+            url = "https://api.fxpricing.com/v1/prices"
+            params = {"instrument": pair, "period": interval, "count": limit}
+
+            async with aiohttp.ClientSession(
+                timeout=aiohttp.ClientTimeout(total=30)
+            ) as session:
+                async with session.get(url, params=params) as response:
+                    if response.status != 200:
+                        logger.error("Free API error: %s", response.status)
+                        return None
+                    data = await response.json()
+
+                    df_data = []
+                    for item in data.get("prices", []):
+                        try:
+                            df_data.append(
+                                {
+                                    "timestamp": pd.to_datetime(item["time"]),
+                                    "Open": float(item["open"]),
+                                    "High": float(item["high"]),
+                                    "Low": float(item["low"]),
+                                    "Close": float(item["close"]),
+                                }
+                            )
+                        except (KeyError, ValueError):
+                            continue
+
+                    if not df_data:
+                        return None
+
+                    df = pd.DataFrame(df_data)
+                    df.set_index("timestamp", inplace=True)
+                    df.sort_index(inplace=True)
+
+                    logger.info(
+                        "✅ Fetched %s candles for %s from Free API", len(df), pair
+                    )
+                    return df
+        except Exception as exc:
+            logger.error("Error fetching free API data for %s: %s", pair, exc)
+            return None
+
+    # METHOD 4: Fallback Mock Data (FOR TESTING)
+    async def _get_ohlc_data_mock(
+        self, pair: str, timeframe: str = "1H", limit: int = 100
+    ) -> Optional[pd.DataFrame]:
+        """Generate mock OHLC data for testing purposes"""
+        try:
+            import numpy as np
+
+            np.random.seed(42)
+            base_prices = {
+                "EURUSD": 1.0800,
+                "GBPUSD": 1.2500,
+                "USDJPY": 150.00,
+                "AUDUSD": 0.6500,
+                "USDCAD": 1.3500,
+                "USDCHF": 0.9000,
+                "NZDUSD": 0.6000,
+            }
+            base_price = base_prices.get(pair, 1.0000)
+
+            end_time = datetime.now()
+            if timeframe == "1M":
+                freq = "1T"
+            elif timeframe == "5M":
+                freq = "5T"
+            elif timeframe == "15M":
+                freq = "15T"
+            elif timeframe == "30M":
+                freq = "30T"
+            elif timeframe == "1H":
+                freq = "1H"
+            elif timeframe == "4H":
+                freq = "4H"
+            else:
+                freq = "1D"
+
+            timestamps = pd.date_range(end=end_time, periods=limit, freq=freq)
+
+            df_data = []
+            current_price = base_price
+            for timestamp in timestamps:
+                price_change = np.random.normal(0, 0.001) * current_price
+                open_price = current_price
+                close_price = current_price + price_change
+                high_price = max(open_price, close_price) + abs(
+                    np.random.normal(0, 0.0005)
+                ) * current_price
+                low_price = min(open_price, close_price) - abs(
+                    np.random.normal(0, 0.0005)
+                ) * current_price
+                df_data.append(
+                    {
+                        "timestamp": timestamp,
+                        "Open": round(open_price, 5),
+                        "High": round(high_price, 5),
+                        "Low": round(low_price, 5),
+                        "Close": round(close_price, 5),
+                    }
+                )
+                current_price = close_price
+
+            df = pd.DataFrame(df_data)
+            df.set_index("timestamp", inplace=True)
+            logger.info("✅ Generated %s mock candles for %s", len(df), pair)
+            return df
+        except Exception as exc:
+            logger.error("Error generating mock data for %s: %s", pair, exc)
+            return None
+
+    # METHOD 5: Yahoo Finance (FREE ALTERNATIVE)
+    async def _get_ohlc_data_yahoo(
+        self, pair: str, timeframe: str = "1H", limit: int = 100
+    ) -> Optional[pd.DataFrame]:
+        """Fetch OHLC data from Yahoo Finance (Free but limited forex pairs)"""
+        try:
+            yahoo_symbol = f"{pair}=X"
+            interval_map = {
+                "1M": "1m",
+                "5M": "5m",
+                "15M": "15m",
+                "30M": "30m",
+                "1H": "1h",
+                "1D": "1d",
+            }
+            interval = interval_map.get(timeframe, "1h")
+
+            if timeframe in ["1M", "5M"]:
+                period = "7d"
+            elif timeframe in ["15M", "30M", "1H"]:
+                period = "60d"
+            else:
+                period = "1y"
+
+            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
+            params = {
+                "interval": interval,
+                "period1": int((datetime.now() - timedelta(days=30)).timestamp()),
+                "period2": int(datetime.now().timestamp()),
+                "includePrePost": "false",
+            }
+
+            async with aiohttp.ClientSession(
+                timeout=aiohttp.ClientTimeout(total=30)
+            ) as session:
+                async with session.get(url, params=params) as response:
+                    if response.status != 200:
+                        logger.error("Yahoo Finance API error: %s", response.status)
+                        return None
+                    data = await response.json()
+
+                    if "chart" not in data or not data["chart"]["result"]:
+                        logger.error("No chart data from Yahoo Finance for %s", pair)
+                        return None
+                    result = data["chart"]["result"][0]
+                    timestamps = result["timestamp"]
+                    ohlc_data = result["indicators"]["quote"][0]
+
+                    df_data = []
+                    for i, ts in enumerate(timestamps):
+                        try:
+                            df_data.append(
+                                {
+                                    "timestamp": pd.to_datetime(ts, unit="s"),
+                                    "Open": float(ohlc_data["open"][i]),
+                                    "High": float(ohlc_data["high"][i]),
+                                    "Low": float(ohlc_data["low"][i]),
+                                    "Close": float(ohlc_data["close"][i]),
+                                }
+                            )
+                        except (TypeError, ValueError, IndexError):
+                            continue
+
+                    if not df_data:
+                        logger.error("No valid data from Yahoo Finance for %s", pair)
+                        return None
+
+                    df = pd.DataFrame(df_data)
+                    df.set_index("timestamp", inplace=True)
+                    df.sort_index(inplace=True)
+                    if len(df) > limit:
+                        df = df.tail(limit)
+
+                    logger.info(
+                        "✅ Fetched %s candles for %s from Yahoo Finance",
+                        len(df),
+                        pair,
+                    )
+                    return df
+        except Exception as exc:
+            logger.error("Error fetching Yahoo Finance data for %s: %s", pair, exc)
+            return None
+
+    # MAIN METHOD - Choose your data source
+    async def _get_ohlc_data(
+        self, pair: str, timeframe: str = "1H", limit: int = 100
+    ) -> Optional[pd.DataFrame]:
+        """Main data fetching method with fallback strategy"""
+        methods = [
+            # ("Yahoo Finance", self._get_ohlc_data_yahoo),
+            # ("Alpha Vantage", self._get_ohlc_data_alpha_vantage),
+            # ("OANDA", self._get_ohlc_data_oanda),
+            ("Mock Data", self._get_ohlc_data_mock),
+        ]
+
+        for method_name, method_func in methods:
+            try:
+                logger.info("Trying %s for %s", method_name, pair)
+                df = await method_func(pair, timeframe, limit)
+                if df is not None and not df.empty:
+                    logger.info(
+                        "✅ Successfully fetched data using %s", method_name
+                    )
+                    return df
+                logger.warning(
+                    "❌ %s returned empty data for %s", method_name, pair
+                )
+            except Exception as exc:
+                logger.error("❌ %s failed for %s: %s", method_name, pair, exc)
+                continue
+
+        logger.error("❌ All data sources failed for %s", pair)
+        return None
+
+
+"""Integration instructions for your CloudBot class:
+
+1. Add this to your CloudBot __init__ method:
+   self.data_integration = CloudBotDataIntegration()
+
+2. Replace your _get_ohlc_data method with:
+   async def _get_ohlc_data(self, pair: str, timeframe: str = '1H', limit: int = 100):
+       return await self.data_integration._get_ohlc_data(pair, timeframe, limit)
+
+3. Set environment variables for API keys:
+   export ALPHA_VANTAGE_API_KEY="your_key_here"
+   export OANDA_API_KEY="your_key_here"
+   export OANDA_ACCOUNT_ID="your_account_id"
+
+4. Install required packages:
+   pip install aiohttp pandas numpy
+
+5. Choose your preferred data source by editing the methods list in _get_ohlc_data()
+"""
