import requests
from config import TWELVE_API_KEY

def get_ohlc(symbol, interval="1h", outputsize=200):
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": symbol, "interval": interval, "outputsize": outputsize, "apikey": TWELVE_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("values", [])
    except Exception as e:
        print(f"[Error] Failed to fetch OHLC for {symbol}: {e}")
        return []

def get_price(symbol):
    data = get_ohlc(symbol, interval="1min", outputsize=1)
    if data:
        return float(data[0]['close'])
    return None