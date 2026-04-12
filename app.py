import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time
import requests
from PIL import Image
from io import BytesIO

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Stock Vision", layout="wide")

# =========================
# SAFE DATA FETCH (NO CACHE BUG)
# =========================
@st.cache_data(ttl=120)
def get_data(symbol, period):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        if data.empty:
            return None
        return data
    except:
        return None

# =========================
# CUSTOM CSS (UNCHANGED)
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
    transform: translateY(-10px) scale(1.05);
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
stock2 = st.sidebar.text_input("Stock/ETF 2 (Optional)", "").upper()
period = st.sidebar.selectbox("Select Time Period", ["1mo", "6mo", "1y", "5y"], index=2)

# =========================
# TITLE
# =========================
st.title("📊 Stock Vision")

tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Charts", "⚖️ Comparison"])

# =========================
# FETCH DATA
# =========================
data1 = get_data(stock1, period)

if data1 is None or len(data1) < 2:
    st.error("⚠️ Unable to fetch enough data.")
    st.stop()

ticker1 = yf.Ticker(stock1)

data2 = get_data(stock2, period) if stock2 else None

data = data1

# =========================
# INDICATORS (SAFE)
# =========================
data["MA50"] = data["Close"].rolling(min(50, len(data))).mean()
data["MA100"] = data["Close"].rolling(min(100, len(data))).mean()

delta = data["Close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / (loss + 1e-9)
data["RSI"] = 100 - (100 / (1 + rs))

# =========================
# TAB 1: OVERVIEW
# =========================
with tab1:
    st.subheader("Company Info")

    try:
        info = ticker1.info
    except:
        info = {}

    st.write("Name:", info.get("longName", "N/A"))
    st.write("Sector:", info.get("sector", "N/A"))

# =========================
# TAB 2: CHARTS (ALL BACK ✅)
# =========================
with tab2:

    # 🔹 PRICE CHART
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

    fig.update_layout(template="plotly_dark", title="Price Chart")
    st.plotly_chart(fig)

    # 🔹 VOLUME CHART
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Bar(x=data.index, y=data["Volume"]))
    fig_vol.update_layout(template="plotly_dark", title="Volume")
    st.plotly_chart(fig_vol)

    # 🔹 RSI CHART
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI"))
    fig_rsi.add_hline(y=70)
    fig_rsi.add_hline(y=30)
    fig_rsi.update_layout(template="plotly_dark", title="RSI Indicator")
    st.plotly_chart(fig_rsi)

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

    fig.update_layout(template="plotly_dark", title="Comparison")
    st.plotly_chart(fig)
