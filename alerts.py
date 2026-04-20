import yfinance as yf
import requests
import time
from datetime import datetime
import pytz

# ============================================================
#  FILL IN YOUR DETAILS HERE
# ============================================================
TOKEN   = "8759368802:AAHcKUrO30kYQmSnCqiSy4hYRlQGR9qRH7w"    # e.g. 8759368802:AAHcKU...
CHAT_ID = "1137332542"  # e.g. 123456789
# ============================================================

IST = pytz.timezone("Asia/Kolkata")
POLL_INTERVAL = 180  # seconds between each scan (3 minutes)

# Full NSE F&O stocks list
SYMBOLS = [
    "AARTIIND.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", "ABFRL.NS",
    "ACC.NS", "ADANIENT.NS", "ADANIPORTS.NS", "ALKEM.NS", "AMARAJABAT.NS",
    "AMBUJACEM.NS", "APOLLOHOSP.NS", "APOLLOTYRE.NS", "ASHOKLEY.NS", "ASIANPAINT.NS",
    "ASTRAL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS", "BALKRISIND.NS", "BANDHANBNK.NS",
    "BANKBARODA.NS", "BATAINDIA.NS", "BEL.NS", "BERGEPAINT.NS", "BHARATFORG.NS",
    "BHARTIARTL.NS", "BHEL.NS", "BIOCON.NS", "BOSCHLTD.NS", "BPCL.NS",
    "BRITANNIA.NS", "BSOFT.NS", "CANBK.NS", "CANFINHOME.NS", "CHAMBLFERT.NS",
    "CHOLAFIN.NS", "CIPLA.NS", "COALINDIA.NS", "COFORGE.NS", "COLPAL.NS",
    "CONCOR.NS", "COROMANDEL.NS", "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS",
    "DABUR.NS", "DALBHARAT.NS", "DEEPAKNTR.NS", "DELTACORP.NS", "DIVISLAB.NS",
    "DIXON.NS", "DLF.NS", "DRREDDY.NS", "EICHERMOT.NS", "ESCORTS.NS",
    "EXIDEIND.NS", "FEDERALBNK.NS", "FINNIFTY.NS", "FORTIS.NS", "GAIL.NS",
    "GLENMARK.NS", "GMRINFRA.NS", "GNFC.NS", "GODREJCP.NS", "GODREJPROP.NS",
    "GRANULES.NS", "GRASIM.NS", "GUJGASLTD.NS", "HAL.NS", "HAVELLS.NS",
    "HCLTECH.NS", "HDFCAMC.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS",
    "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
    "ICICIGI.NS", "ICICIPRULI.NS", "IDEA.NS", "IDFC.NS", "IDFCFIRSTB.NS",
    "IEX.NS", "IGL.NS", "INDHOTEL.NS", "INDIAMART.NS", "INDIANB.NS",
    "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", "INFY.NS", "IOC.NS",
    "IPCALAB.NS", "IRCTC.NS", "ITC.NS", "JINDALSTEL.NS", "JKCEMENT.NS",
    "JSL.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", "KOTAKBANK.NS", "LALPATHLAB.NS",
    "LAURUSLABS.NS", "LICHSGFIN.NS", "LT.NS", "LTIM.NS", "LTTS.NS",
    "LUPIN.NS", "M&M.NS", "M&MFIN.NS", "MANAPPURAM.NS", "MARICO.NS",
    "MARUTI.NS", "MCDOWELL-N.NS", "MCX.NS", "METROPOLIS.NS", "MFSL.NS",
    "MGL.NS", "MOTHERSON.NS", "MPHASIS.NS", "MRF.NS", "MUTHOOTFIN.NS",
    "NATIONALUM.NS", "NAUKRI.NS", "NAVINFLUOR.NS", "NESTLEIND.NS", "NMDC.NS",
    "NTPC.NS", "OBEROIRLTY.NS", "OFSS.NS", "ONGC.NS", "PAGEIND.NS",
    "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PIDILITIND.NS",
    "PIIND.NS", "PNB.NS", "POLYCAB.NS", "POWERGRID.NS", "PVRINOX.NS",
    "RAMCOCEM.NS", "RBLBANK.NS", "RECLTD.NS", "RELIANCE.NS", "SAIL.NS",
    "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", "SHRIRAMFIN.NS",
    "SIEMENS.NS", "SRF.NS", "STAR.NS", "SUNPHARMA.NS", "SUNTV.NS",
    "SUPREMEIND.NS", "SYNGENE.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS",
    "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS",
    "TORNTPHARM.NS", "TORNTPOWER.NS", "TRENT.NS", "TVSMOTOR.NS", "UBL.NS",
    "ULTRACEMCO.NS", "UPL.NS", "VEDL.NS", "VOLTAS.NS", "WIPRO.NS",
    "WOCKPHARMA.NS", "ZEEL.NS", "ZYDUSLIFE.NS"
]

# Tracks last known state per symbol
# States: "above_high" | "above_low" | "below_low" | None (startup)
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

def get_price_state(price, prev_high, prev_low):
    if price > prev_high:
        return "above_high"
    elif price < prev_low:
        return "below_low"
    else:
        return "above_low"   # sitting between low and high

def get_prev_month_levels(symbol):
    try:
        ticker  = yf.Ticker(symbol)
        monthly = ticker.history(period="3mo", interval="1mo")
        if len(monthly) < 2:
            return None, None
        prev_high = round(float(monthly["High"].iloc[-2]), 2)
        prev_low  = round(float(monthly["Low"].iloc[-2]),  2)
        return prev_high, prev_low
    except Exception as e:
        print(f"Error fetching monthly data for {symbol}: {e}")
        return None, None

def get_live_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data   = ticker.history(period="1d", interval="1m")
        if data.empty:
            return None
        return round(float(data["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"Error fetching live price for {symbol}: {e}")
        return None

def check_symbol(symbol, prev_high, prev_low):
    name  = symbol.replace(".NS", "")
    price = get_live_price(symbol)
    if price is None:
        return

    now       = datetime.now(IST).strftime("%H:%M")
    new_state = get_price_state(price, prev_high, prev_low)
    old_state = last_state.get(symbol)   # None on very first check

    print(f"{now} | {name:15s} | ₹{price:>10.2f} | {old_state or 'init':12s} → {new_state}")

    # First check of the day — just record state, no alert
    if old_state is None:
        last_state[symbol] = new_state
        return

    # No change — do nothing
    if new_state == old_state:
        return

    # State changed — update and alert
    last_state[symbol] = new_state

    if new_state == "above_high":
        send_alert(
            f"🚨 <b>{name}</b> [{now}]\n"
            f"Crossed ABOVE Prev Month High\n"
            f"Price: ₹{price} | PMH: ₹{prev_high}"
        )

    elif new_state == "above_low" and old_state == "below_low":
        send_alert(
            f"⚠️ <b>{name}</b> [{now}]\n"
            f"Crossed ABOVE Prev Month Low\n"
            f"Price: ₹{price} | PML: ₹{prev_low}"
        )

    elif new_state == "above_low" and old_state == "above_high":
        send_alert(
            f"↘️ <b>{name}</b> [{now}]\n"
            f"Dropped BACK BELOW Prev Month High\n"
            f"Price: ₹{price} | PMH: ₹{prev_high}"
        )

    elif new_state == "below_low":
        send_alert(
            f"🔴 <b>{name}</b> [{now}]\n"
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
    print("Daily state reset — first scan of new day will re-establish baselines.")

# ─────────────────────────────────────────────
#  STARTUP
# ─────────────────────────────────────────────
print("=" * 55)
print("  NSE F&O Alert Bot — Starting Up")
print("=" * 55)
print(f"Fetching previous month levels for {len(SYMBOLS)} symbols...")
print("(This may take 1-2 minutes)\n")

levels = {}
failed = []
for sym in SYMBOLS:
    ph, pl = get_prev_month_levels(sym)
    if ph and pl:
        levels[sym] = (ph, pl)
        print(f"  ✓ {sym.replace('.NS',''):15s}  PMH={ph}  PML={pl}")
    else:
        failed.append(sym)
        print(f"  ✗ {sym} — skipped (no data)")

print(f"\nReady: {len(levels)} symbols loaded, {len(failed)} skipped.")
send_alert(
    f"✅ <b>Alert Bot Started</b>\n"
    f"Monitoring {len(levels)} F&O stocks\n"
    f"Alert fires on EVERY crossing (state change)\n"
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
        print(f"Scan complete. Next in {POLL_INTERVAL//60} min.")
        time.sleep(POLL_INTERVAL)
    else:
        print(f"[{now_ist.strftime('%H:%M:%S')}] Market closed — sleeping 5 min...")
        time.sleep(300)
