import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 基本配置 ---
st.set_page_config(page_title="投資監測儀表板", layout="wide")
st.title("📈 投資新手全方位監測站")

# --- 2. 側邊欄 ---
st.sidebar.header("🔍 股票查詢")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()

# --- 3. 數據抓取函數 ---
@st.cache_data(ttl=3600)
def load_full_data(tk):
    stock = yf.Ticker(tk)
    return {
        "info": stock.info,
        "hist": stock.history(period="1y"),
        "divs": stock.dividends,
        "income": stock.financials,
        "balance": stock.balance_sheet,
        "cash": stock.cashflow
    }

# --- 4. 主程式 ---
try:
    with st.spinner('數據同步中...'):
        d = load_full_data(symbol)
        info, hist = d["info"], d["hist"]

    if hist.empty:
        st.error("找不到該代號數據，請重新確認。")
    else:
        # --- A. 核心卡片 ---
        c1, c2, c3, c4 = st.columns(4)
        price = info.get('currentPrice') or hist['Close'].iloc[-1]
        p_close = info.get('previousClose') or hist['Close'].iloc[0]
        diff = ((price - p_close) / p_close) * 100
        m_cap = (info.get('marketCap', 0) / 1000000000)

        c1.metric("當前股價", f"${price:,.2f}", f"{diff:+.2f}%")
        c2.metric("本益比 (P/E)", info.get('trailingPE', 'N/A'))
        c3.metric("市值 (B)", f"{m_cap:,.1f}B")
        c4.metric("52週高點", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")

        # --- B. 走勢圖 ---
        st.subheader("📊 價格走勢")
        fig = go.Figure(go.Scatter(x=hist.index, y=hist['Close'], name='收盤價'))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # --- C. 功能分頁 ---
        t1, t2, t3 = st.tabs(["💰 殖利率", "🐻 做空監測", "📄 財報視窗"])

        with t1:
            dv = d["divs"]
            if not dv.empty:
                total_div = dv.last('365D').sum()
                y_rate = (total_div / price) * 100 if price > 0 else 0
                st.write(f"**過去一年總配息：** ${total_div:.2f}")
                st.metric("預估殖利率", f"{y_rate:.2f}%")
                st.bar_chart(dv.tail(8))
            else:
                st.info("該標的無近期配息數據。")

        with t2:
            s_
