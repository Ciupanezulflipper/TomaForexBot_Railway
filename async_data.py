# async_data.py
import aiohttp

async def fetch_symbol_data(session, symbol):
    url = f"https://api.example.com/price/{symbol}"
    async with session.get(url) as resp:
        data = await resp.json()
        return data

async def fetch_multiple_symbols(symbols):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_symbol_data(session, sym) for sym in symbols]
        return await asyncio.gather(*tasks)
