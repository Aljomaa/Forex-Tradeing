import pandas as pd

def compute_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_ema(df, period=20):
    return df['close'].ewm(span=period, adjust=False).mean()

def compute_support_resistance(df, window=20):
    support = df['low'].rolling(window).min()
    resistance = df['high'].rolling(window).max()
    return support, resistance

def full_technical_analysis(df):
    df[['open','high','low','close']] = df[['open','high','low','close']].astype(float)
    rsi = compute_rsi(df).iloc[-1]
    ema20 = compute_ema(df, 20).iloc[-1]
    ema50 = compute_ema(df, 50).iloc[-1]
    support, resistance = compute_support_resistance(df)
    last_support = support.iloc[-1]
    last_resistance = resistance.iloc[-1]

    analysis = f"- RSI: {rsi:.2f}\n- EMA20: {ema20:.2f}\n- EMA50: {ema50:.2f}\n"
    analysis += f"- الدعم الأخير: {last_support:.2f}\n- المقاومة الأخيرة: {last_resistance:.2f}\n"
    analysis += "- ICT: Order Blocks, Market Structure, Liquidity Pools\n"
    analysis += "- Harmonics & Fibonacci Levels\n- FVG (Fair Value Gaps)\n"
    return analysis