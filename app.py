import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="stock vision", layout="wide")

# =========================
# 🔥 CACHE (IMPORTANT FIX)
# =========================
@st.cache_data(ttl=60)
def get_data(symbol, period):
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period), ticker

# =========================
# CUSTOM CSS (UNCHANGED)
# =========================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
<style>
.main { background-color: #0e1117; color: white; font-family: 'Roboto', sans-serif; }
h1, h2, h3 { color: #00ffcc; }

.metric-card {
    background: linear-gradient(135deg, #1a1f2b, #0e1117);
    border-radius: 15px;
    padding: 16px;
    box-shadow: 0 8px 20px rgba(0,255,204,0.3);
    text-align: center;
    transition: transform 0.3s ease, box-shadow 0.3s ease, background-color 0.3s ease;
}
.metric-card:hover {
    transform: translateY(-10px) scale(1.05);
    box-shadow: 0 16px 30px rgba(0,255,204,0.5);
    background-color: #111826;
}
.metric-title { font-weight: 600; font-size: 1.1rem; }
.metric-value { font-weight: 700; font-size: 1.9rem; }
.metric-change { font-size: 1rem; }
.tab-content {
    background: linear-gradient(135deg, #0e1117, #1a1f2b);
    padding: 20px;
    border-radius: 12px;
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

stock1 = st.sidebar.text_input("Stock/ETF 1", st.session_state.get('stock1','TCS.NS')).upper()
stock2 = st.sidebar.text_input("Stock/ETF 2 (Optional)", "").upper().strip()
period = st.sidebar.selectbox("Select Time Period", ["1mo", "6mo", "1y", "5y"], index=2)
auto_refresh = st.sidebar.checkbox("Enable Auto Refresh")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)

# =========================
# TITLE
# =========================
st.title("🚀 Pro Stock & ETF Dashboard")
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Charts", "⚖️ Comparison"])

# =========================
# FETCH DATA (FIXED)
# =========================
with st.spinner("Fetching data..."):
    try:
        data1, ticker1 = get_data(stock1, period)
        data2, ticker2 = (get_data(stock2, period) if stock2 else (None, None))
    except Exception as e:
        st.error("⚠️ Error fetching data. Please try again later.")
        st.stop()

data = data1
ticker = ticker1

if data.empty:
    st.error("No data found")
else:
    # =========================
    # INDICATORS
    # =========================
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA100"] = data["Close"].rolling(100).mean()

    delta = data["Close"].diff()
    gain = (delta.where(delta>0,0)).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rs = gain/loss
    data["RSI"] = 100-(100/(1+rs))

    # =========================
    # TAB 1
    # =========================
    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        info = ticker.info

        st.subheader("🏢 Company / ETF Info")
        col1, col2, col3 = st.columns(3)

        logo_img = None
        logo_url = info.get('logo_url','')
        if logo_url:
            try:
                response = requests.get(logo_url, timeout=3)
                if response.status_code == 200:
                    logo_img = Image.open(BytesIO(response.content))
            except:
                pass

        with col1:
            if logo_img:
                st.image(logo_img, width=100)
            st.write(f"**Name:** {info.get('longName','N/A')}")
            st.write(f"**Sector:** {info.get('sector','N/A')}")
        with col2:
            st.write(f"**Market Cap:** {info.get('marketCap','N/A')}")
            st.write(f"**Country:** {info.get('country','N/A')}")
        with col3:
            st.write(f"**Currency:** {info.get('currency','N/A')}")
            st.write(f"**Exchange:** {info.get('exchange','N/A')}")

        st.markdown("---")

        col1, col2, col3 = st.columns(3)
        price = data["Close"].iloc[-1]
        prev = data["Close"].iloc[-2]
        change = price-prev
        pct = (change/prev)*100

        trend = "Bullish" if data["MA50"].iloc[-1]>data["MA100"].iloc[-1] else "Bearish"
        rsi = data["RSI"].iloc[-1]
        rsi_status = "Overbought" if rsi>70 else ("Oversold" if rsi<30 else "Neutral")

        with col1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>💰 Price</div><div class='metric-value'>{round(price,2)}</div><div class='metric-change'>{round(change,2)} ({round(pct,2)}%)</div></div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>📈 Trend</div><div class='metric-value'>{trend}</div></div>", unsafe_allow_html=True)

        with col3:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>RSI</div><div class='metric-value'>{round(rsi,2)}</div><div class='metric-change'>{rsi_status}</div></div>", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # TAB 2 (UNCHANGED)
    # =========================
    with tab2:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data.index, open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"]
        ))
        fig.add_trace(go.Scatter(x=data.index, y=data["MA50"], name="MA50"))
        fig.add_trace(go.Scatter(x=data.index, y=data["MA100"], name="MA100"))
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig)

        st.markdown('</div>', unsafe_allow_html=True)

    # =========================
    # TAB 3
    # =========================
    with tab3:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(x=data1.index, y=data1["Close"], name=stock1))

        if data2 is not None and not data2.empty:
            fig_compare.add_trace(go.Scatter(x=data2.index, y=data2["Close"], name=stock2))
        else:
            st.info("Enter second stock/ETF to compare")

        fig_compare.update_layout(template="plotly_dark")
        st.plotly_chart(fig_compare)

        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# AUTO REFRESH
# =========================
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()
