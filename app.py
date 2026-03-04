import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 基礎配置 ---
st.set_page_config(page_title="投資監測站", layout="wide")
st.title("📈 投資新手全方位監測儀表板")

# --- 2. 側邊欄 ---
st.sidebar.header("🔍 查詢設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()

# --- 3. 數據抓取 (快取優化) ---
@st.cache_data(ttl=3600)
def load_data(tk):
    stock = yf.Ticker(tk)
    # 抓取基本資訊、歷史價、財報、股利
    return {
        "info": stock.info,
        "hist": stock.history(period="1y"),
        "divs": stock.dividends,
        "income": stock.financials,
        "balance": stock.balance_sheet,
        "cash": stock.cashflow
    }

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('讀取中...'):
        data = load_data(symbol)
        info = data["info"]
        hist = data["hist"]

    if hist.empty:
        st.error("找不到代號，請確認輸入正確。")
    else:
        # --- 指標區 (拆解長度避免報錯) ---
        c1, c2, c3, c4 = st.columns(4)
        
        # 股價計算
        price = info.get('currentPrice') or hist['Close'].iloc[-1]
        p_close = info.get('previousClose') or hist['Close'].iloc[0]
        diff = ((price - p_close) / p_close) * 100
        
        # 市值計算 (拆開寫防止截斷)
        m_cap = info.get('marketCap', 0)
        m_cap_billion = m_cap / 1000000000
        
        c1.metric("價格", f"${price:,.2f}", f"{diff:+.2f}%")
        c2.metric("P/E", info.get('trailingPE', 'N/A'))
        c3.metric("市值 (B)", f"{m_cap_billion:,.1f}B")
        c4.metric("52W高點", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")

        # --- 圖表區 ---
        st.subheader("📊 價格走勢")
        fig = go.Figure(go.Scatter(x=hist.index, y=hist['Close'], name='Close'))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # --- 分頁區 ---
        t1, t2, t3 = st.tabs(["💰 殖利率", "🐻 做空", "📄 財報"])

        with t1:
            dv = data["divs"]
            if not dv.empty:
                y_val = (dv.last('365D').sum() / price) * 100
                st.metric("預估殖利率", f"{y_val:.2f}%")
                st.bar_chart(dv.tail(8))
            else:
                st.info("無配息數據")

        with t2:
            s_pct = info.get('shortPercentOfFloat', 0) * 100
            s_day = info.get('shortRatio', "N/A")
            st.metric("空單佔比", f"{s_pct:.2f}%")
            st.write(f"回補天數: {s_day}")
            if s_pct > 10:
                st.warning("⚠️ 空方壓力較大")

        with t3:
            choice = st.radio("報表", ["損益", "資產", "現金"], horizontal=True)
            if choice == "損益":
                df = data["income"]
            elif choice == "資產":
                df = data["balance"]
            else:
