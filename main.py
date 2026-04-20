import requests
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import pytz
from nsepython import nse_eq, equity_history

# ============================================================
#  FILL IN YOUR DETAILS HERE
# ============================================================
TOKEN   = "8759368802:AAHcKUrO30kYQmSnCqiSy4hYRlQGR9qRH7w"
CHAT_ID = "1137332542"
# ============================================================

IST           = pytz.timezone("Asia/Kolkata")
POLL_INTERVAL = 180  # seconds (3 minutes)

SYMBOLS = [
    "AARTIIND", "ABB", "ABBOTINDIA", "ABCAPITAL", "ABFRL",
    "ACC", "ADANIENT", "ADANIPORTS", "ALKEM", "AMBUJACEM",
    "APOLLOHOSP", "APOLLOTYRE", "ASHOKLEY", "ASIANPAINT",
    "ASTRAL", "ATUL", "AUBANK", "AUROPHARMA", "AXISBANK",
    "BAJAJ-AUTO", "BAJAJFINSV", "BAJFINANCE", "BALKRISIND", "BANDHANBNK",
    "BANKBARODA", "BATAINDIA", "BEL", "BERGEPAINT", "BHARATFORG",
    "BHARTIARTL", "BHEL", "BIOCON", "BOSCHLTD", "BPCL",
    "BRITANNIA", "BSOFT", "CANBK", "CANFINHOME", "CHAMBLFERT",
    "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL",
    "CONCOR", "COROMANDEL", "CROMPTON", "CUB", "CUMMINSIND",
    "DABUR", "DALBHARAT", "DEEPAKNTR", "DELTACORP", "DIVISLAB",
    "DIXON", "DLF", "DRREDDY", "EICHERMOT", "ESCORTS",
    "EXIDEIND", "FEDERALBNK", "FORTIS", "GAIL",
    "GLENMARK", "GMRINFRA", "GNFC", "GODREJCP", "GODREJPROP",
    "GRANULES", "GRASIM", "GUJGASLTD", "HAL", "HAVELLS",
    "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO",
    "HINDALCO", "HINDCOPPER", "HINDPETRO", "HINDUNILVR", "ICICIBANK",
    "ICICIGI", "ICICIPRULI", "IDEA", "IDFC", "IDFCFIRSTB",
    "IEX", "IGL", "INDHOTEL", "INDIAMART", "INDIANB",
    "INDIGO", "INDUSINDBK", "INDUSTOWER", "INFY", "IOC",
    "IPCALAB", "IRCTC", "ITC", "JINDALSTEL", "JKCEMENT",
    "JSL", "JSWSTEEL", "JUBLFOOD", "KOTAKBANK", "LALPATHLAB",
    "LAURUSLABS", "LICHSGFIN", "LT", "LTIM", "LTTS",
    "LUPIN", "M&M", "M&MFIN", "MANAPPURAM", "MARICO",
    "MARUTI", "MCDOWELL-N", "MCX", "METROPOLIS", "MFSL",
    "MGL", "MOTHERSON", "MPHASIS", "MRF", "MUTHOOTFIN",
    "NATIONALUM", "NAUKRI", "NAVINFLUOR", "NESTLEIND", "NMDC",
    "NTPC", "OBEROIRLTY", "OFSS", "ONGC", "PAGEIND",
    "PEL", "PERSISTENT", "PETRONET", "PFC", "PIDILITIND",
    "PIIND", "PNB", "POLYCAB", "POWERGRID", "PVRINOX",
    "RAMCOCEM", "RBLBANK", "RECLTD", "RELIANCE", "SAIL",
    "SBICARD", "SBILIFE", "SBIN", "SHREECEM", "SHRIRAMFIN",
    "SIEMENS", "SRF", "SUNPHARMA", "SUNTV",
    "SUPREMEIND", "SYNGENE", "TATACOMM", "TATACONSUM", "TATAMOTORS",
    "TATAPOWER", "TATASTEEL", "TCS", "TECHM", "TITAN",
    "TORNTPHARM", "TORNTPOWER", "TRENT", "TVSMOTOR", "UBL",
    "ULTRACEMCO", "UPL", "VEDL", "VOLTAS", "WIPRO",
    "WOCKPHARMA", "ZEEL", "ZYDUSLIFE"
]

# Tracks last known price zone per symbol
# Zones: "above_high" | "above_low" | "below_low" | None (startup)
last_state = {}

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"Alert send error: {e}")

def get_prev_month_levels(symbol):
    try:
        today     = date.today()
        # Previous month date range
        first_of_this_month  = today.replace(day=1)
        last_of_prev_month   = first_of_this_month - relativedelta(days=1)
        first_of_prev_month  = last_of_prev_month.replace(day=1)

        start_str = first_of_prev_month.strftime("%d-%m-%Y")
        end_str   = last_of_prev_month.strftime("%d-%m-%Y")

        df = equity_history(symbol, "EQ", start_str, end_str)
        if df is None or df.empty:
            return None, None

        prev_high = round(float(df["CH_TRADE_HIGH_PRICE"].max()), 2)
        prev_low  = round(float(df["CH_TRADE_LOW_PRICE"].min()),  2)
        return prev_high, prev_low
    except Exception as e:
        print(f"Error fetching monthly levels for {symbol}: {e}")
        return None, None

def get_live_price(symbol):
    try:
        data  = nse_eq(symbol)
        price = float(data["priceInfo"]["lastPrice"])
        return round(price, 2)
    except Exception as e:
        print(f"Error fetching live price for {symbol}: {e}")
        return None

def get_price_state(price, prev_high, prev_low):
    if price > prev_high:
        return "above_high"
    elif price < prev_low:
        return "below_low"
    else:
        return "above_low"

def check_symbol(symbol, prev_high, prev_low):
    price = get_live_price(symbol)
    if price is None:
        return

    now       = datetime.now(IST).strftime("%H:%M")
    new_state = get_price_state(price, prev_high, prev_low)
    old_state = last_state.get(symbol)

    print(f"{now} | {symbol:15s} | ₹{price:>10.2f} | {old_state or 'init':12s} → {new_state}")

    # First check — just record state, no alert
    if old_state is None:
        last_state[symbol] = new_state
        return

    # No change — do nothing
    if new_state == old_state:
        return

    # State changed — alert
    last_state[symbol] = new_state

    if new_state == "above_high":
        send_alert(
            f"🚨 <b>{symbol}</b> [{now}]\n"
            f"Crossed ABOVE Prev Month High\n"
            f"Price: ₹{price} | PMH: ₹{prev_high}"
        )
    elif new_state == "above_low" and old_state == "below_low":
        send_alert(
            f"⚠️ <b>{symbol}</b> [{now}]\n"
            f"Crossed ABOVE Prev Month Low\n"
            f"Price: ₹{price} | PML: ₹{prev_low}"
        )
    elif new_state == "above_low" and old_state == "above_high":
        send_alert(
            f"↘️ <b>{symbol}</b> [{now}]\n"
            f"Dropped BACK BELOW Prev Month High\n"
            f"Price: ₹{price} | PMH: ₹{prev_high}"
        )
    elif new_state == "below_low":
        send_alert(
            f"🔴 <b>{symbol}</b> [{now}]\n"
            f"Crossed BELOW Prev Month Low\n"
            f"Price: ₹{price} | PML: ₹{prev_low}"
        )

def is_market_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    market_start = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    market_end   = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_start <= now <= market_end

def reset_daily():
    last_state.clear()
    print("Daily state reset.")

# ─────────────────────────────────────────────
#  STARTUP
# ─────────────────────────────────────────────
print("=" * 55)
print("  NSE F&O Alert Bot — Starting Up")
print("=" * 55)
print(f"Fetching previous month levels for {len(SYMBOLS)} symbols...")
print("(This may take a few minutes)\n")

levels = {}
failed = []
for sym in SYMBOLS:
    ph, pl = get_prev_month_levels(sym)
    if ph and pl:
        levels[sym] = (ph, pl)
        print(f"  ✓ {sym:15s}  PMH={ph}  PML={pl}")
    else:
        failed.append(sym)
        print(f"  ✗ {sym} — skipped")
    time.sleep(0.5)  # be polite to NSE servers

print(f"\nReady: {len(levels)} symbols loaded, {len(failed)} skipped.")
send_alert(
    f"✅ <b>Alert Bot Started</b>\n"
    f"Monitoring {len(levels)} F&O stocks\n"
    f"Alerts fire on EVERY crossing\n"
    f"Poll interval: every {POLL_INTERVAL//60} min"
)

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
current_day = datetime.now(IST).date()

while True:
    now_ist = datetime.now(IST)

    if now_ist.date() != current_day:
        reset_daily()
        current_day = now_ist.date()

    if is_market_open():
        print(f"\n[{now_ist.strftime('%H:%M:%S')}] Scanning {len(levels)} symbols...")
        for sym, (ph, pl) in levels.items():
            check_symbol(sym, ph, pl)
            time.sleep(0.3)  # avoid hammering NSE
        print(f"Scan complete. Next in {POLL_INTERVAL//60} min.")
        time.sleep(POLL_INTERVAL)
    else:
        print(f"[{now_ist.strftime('%H:%M:%S')}] Market closed — sleeping 5 min...")
        time.sleep(300)
