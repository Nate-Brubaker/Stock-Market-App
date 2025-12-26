from config import api
import pandas as pd

def get_account_info():
    account = api.get_account()
    return {
        "id": account.id,
        "cash": account.cash,
        "portfolio_value": account.portfolio_value,
        "buying_power": account.buying_power,
        "status": account.status
    }

def get_portfolio_value():
    try:
        return float(api.get_account().portfolio_value)
    except Exception:
        return None

def get_portfolio_history(period="1M", timeframe="1D"):
    try:
        hist = api.get_portfolio_history(period=period, timeframe=timeframe)
        df = pd.DataFrame({
            "Date": pd.to_datetime(hist.timestamp, unit="s"),
            "Close": hist.equity
        })
        df["Date"] = df["Date"].dt.strftime("%m/%d/%y")
        df["Open"] = df["High"] = df["Low"] = df["Close"]
        df["Volume"] = 0
        return df
    except Exception:
        return pd.DataFrame()

def get_holdings():
    try:
        positions = api.list_positions()
        holdings = []
        for pos in positions:
            holdings.append({
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "current_price": float(pos.current_price),
                "market_value": float(pos.market_value),
                "unrealized_pl": float(pos.unrealized_pl)
            })
        return holdings
    except Exception:
        return []

def get_account_element(element):
    account = api.get_account()
    return getattr(account, element, None)

def print_account_summary():
    info = get_account_info()
    print("Account Summary:")
    for key, value in info.items():
        print(f"{key.capitalize()}: {value}")