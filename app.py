import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Pro Stock & ETF Dashboard", layout="wide")

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>
.main { background-color: #0e1117; color: white; }
h1, h2, h3 { color: #00ffcc; }

.metric-card {
    background: linear-gradient(135deg, #1a1f2b, #0e1117);
    border-radius: 15px;
    padding: 16px;
    box-shadow: 0 8px 20px rgba(0,255,204,0.3);
    text-align: center;
    transition: 0.3s;
}
.metric-card:hover {
    transform: scale(1.05);
    box-shadow: 0 16px 30px rgba(0,255,204,0.5);
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
st.sidebar.header("📊 Dashboard Settings")

if 'stock1' not in st.session_state:
    st.session_state['stock1'] = "TCS.NS"

preset_stocks = ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS"]
preset_etfs = ["NIFTYBEES.NS", "GOLDBEES.NS", "BANKBEES.NS"]

st.sidebar.markdown("### Quick Select")
col1, col2 = st.sidebar.columns(2)

for s in preset_stocks:
    if col1.button(s):
        st.session_state['stock1'] = s

for e in preset_etfs:
    if col2.button(e):
        st.session_state['stock1'] = e

stock1 = st.sidebar.text_input("Stock/ETF 1", st.session_state['stock1']).upper()
stock2 = st.sidebar.text_input("Stock/ETF 2 (Optional)", "").upper().strip()
period = st.sidebar.selectbox("Select Time Period", ["1mo", "6mo", "1y", "5y"], index=2)

auto_refresh = st.sidebar.checkbox("Enable Auto Refresh")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)

# =========================
# DATA FETCH (CACHED)
# =========================
@st.cache_data(ttl=300)
def get_data(symbol, period):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period)
    except:
        return None

# =========================
# TITLE
# =========================
st.title("🚀 Pro Stock & ETF Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Charts", "⚖️ Comparison"])

# =========================
# FETCH
# =========================
data1 = get_data(stock1, period)
data2 = get_data(stock2, period) if stock2 else None

if data1 is None or data1.empty:
    st.error("⚠️ Failed to fetch data. Try another stock.")
    st.stop()

data = data1.copy()

# =========================
# INDICATORS
# =========================
data["MA50"] = data["Close"].rolling(50).mean()
data["MA100"] = data["Close"].rolling(100).mean()

delta = data["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data["RSI"] = 100 - (100 / (1 + rs))

# =========================
# TAB 1: OVERVIEW
# =========================
with tab1:
    st.subheader(f"📊 {stock1} Overview")

    price = data["Close"].iloc[-1]
    prev = data["Close"].iloc[-2]
    change = price - prev
    pct = (change / prev) * 100

    trend = "Bullish" if data["MA50"].iloc[-1] > data["MA100"].iloc[-1] else "Bearish"
    rsi = data["RSI"].iloc[-1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
        <h3>💰 Price</h3>
        <h2>{round(price,2)}</h2>
        <p>{round(change,2)} ({round(pct,2)}%)</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
        <h3>📈 Trend</h3>
        <h2>{trend}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
        <h3>RSI</h3>
        <h2>{round(rsi,2)}</h2>
        </div>
        """, unsafe_allow_html=True)

# =========================
# TAB 2: CHARTS
# =========================
with tab2:
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Price"
    ))

    fig.add_trace(go.Scatter(x=data.index, y=data["MA50"], name="MA50"))
    fig.add_trace(go.Scatter(x=data.index, y=data["MA100"], name="MA100"))

    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig)

    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(x=data.index, y=data["Volume"]))
    fig_vol.update_layout(template="plotly_dark")
    st.plotly_chart(fig_vol)

# =========================
# TAB 3: COMPARISON
# =========================
with tab3:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data1.index, y=data1["Close"], name=stock1))

    if data2 is not None and not data2.empty:
        fig.add_trace(go.Scatter(x=data2.index, y=data2["Close"], name=stock2))
    else:
        st.info("Enter second stock to compare")

    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig)

# =========================
# AUTO REFRESH
# =========================
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
