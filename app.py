import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 網頁配置 ---
st.set_page_config(page_title="AI 投資監測站", layout="wide")

st.title("📈 全方位投資監測儀表板")
st.caption("數據來源：Yahoo Finance | 版本：V1.2 (修正快取錯誤)")

# --- 側邊欄設定 ---
st.sidebar.header("🔍 股票查詢")
ticker_symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()

# --- 1. 快取：抓取基本資訊 (info) ---
@st.cache_data(ttl=3600)
def fetch_stock_info(symbol):
    stock = yf.Ticker(symbol)
    return stock.info

# --- 2. 快取：抓取歷史股價 (history) ---
@st.cache_data(ttl=3600)
def fetch_stock_history(symbol, period="1y"):
    stock = yf.Ticker(symbol)
    return stock.history(period=period)

# --- 3. 快取：抓取財務報表與股利 ---
@st.cache_data(ttl=3600)
def fetch_financial_data(symbol):
    stock = yf.Ticker(symbol)
    # 這裡只回傳 DataFrame，這是可以序列化的
    return {
        "dividends": stock.dividends,
        "income_stmt": stock.financials,
        "balance_sheet": stock.balance_sheet,
        "cashflow": stock.cashflow
    }

# --- 主程式執行 ---
try:
    with st.spinner('正在從伺服器獲取最新數據...'):
        # 分開獲取數據，避免快取 Ticker 物件
        info = fetch_stock_info(ticker_symbol)
        hist_data = fetch_stock_history(ticker_symbol)
        fin_data = fetch_financial_data(ticker_symbol)

    if hist_data.empty:
        st.error("找不到數據，請確認代號正確。")
    else:
        # --- 頁面佈局：核心指標 ---
        col1, col2, col3, col4 = st.columns(4)
        curr_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
        prev_close = info.get('previousClose', hist_data['Close'].iloc[0])
        price_chg = ((curr_price - prev_close) / prev_close) * 100

        col1.metric("當前股價", f"${curr_price:,.2f}", f"{price_chg:+.2f}%")
        col2.metric("本益比 (P/E)", info.get('trailingPE', 'N/A'))
        col3.metric("市值", f"{info.get('marketCap', 0)/1e9:,.2f}B")
        col4.metric("52週高點", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")

        # --- 股價走勢圖 ---
        st.subheader("📊 價格走勢")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Close'], name='收盤價'))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # --- 功能分頁 ---
        tab1, tab2, tab3 = st.tabs(["💰 殖利率視窗", "🐻 做空監測", "📄 財報視窗"])

        with tab1:
            st.subheader("股利與年利率分析")
            divs = fin_data["dividends"]
            if not divs.empty:
                last_year_div = divs.last('365D').sum()
                st.write(f"**過去一年總配息：** ${last_year_div:.2f}")
                st.write(f"**預估殖利率：** {(last_year_div/curr_price)*100:.2f}%")
                st.bar_chart(divs.tail(10))
            else:
                st.info("暫無配息數據。")

        with tab2:
            st.subheader("市場做空壓力")
            short_p = info.get('shortPercentOfFloat', 0) * 100
            s_ratio = info.get('shortRatio', "N/A")
            st.metric("空單佔流通股比", f"{short_p:.2f}%")
            st.write(f"**空單回補天數 (Days to Cover)：** {s_ratio}")
            
            if short_p > 10:
                st.warning("⚠️ 空方壓力較大，需留意是否有軋空或利空消息。")
            else:
                st.success("✅ 籌碼面目前相對穩定。")

        with tab3:
            st.subheader("公司年度報表")
            report = st.radio("選擇類型", ["損益表", "資產負債表", "現金流量表"], horizontal=True)
            
            if report == "損益表":
                df = fin_
