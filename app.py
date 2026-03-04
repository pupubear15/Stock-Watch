import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 網頁配置 ---
st.set_page_config(page_title="投資新手監測站", layout="wide")

st.title("📈 投資新手全方位監測儀表板")
st.caption("數據來源：Yahoo Finance | 修正：解決序列化與語法錯誤")

# --- 2. 側邊欄：輸入設定 ---
st.sidebar.header("🔍 股票查詢")
ticker_symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()

# --- 3. 數據抓取函數 (避開序列化錯誤) ---
@st.cache_data(ttl=3600)
def fetch_stock_basic(symbol):
    """獲取基本資訊與股價歷史"""
    stock = yf.Ticker(symbol)
    return stock.info, stock.history(period="1y")

@st.cache_data(ttl=3600)
def fetch_stock_financials(symbol):
    """獲取財務報表與股利 (回傳 Dict/DataFrame 以利快取)"""
    stock = yf.Ticker(symbol)
    return {
        "dividends": stock.dividends,
        "income": stock.financials,
        "balance": stock.balance_sheet,
        "cashflow": stock.cashflow
    }

# --- 4. 主程式邏輯 (使用完整的 try-except 結構) ---
try:
    with st.spinner('數據讀取中...'):
        # 獲取資料
        info, hist_data = fetch_stock_basic(ticker_symbol)
        fin_data = fetch_stock_financials(ticker_symbol)

    if hist_data.empty:
        st.error("找不到數據，請確認代號正確（台股請加 .TW）。")
    else:
        # --- A. 核心指標區 ---
        col1, col2, col3, col4 = st.columns(4)
        curr_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
        prev_close = info.get('previousClose', hist_data['Close'].iloc[0])
        price_chg = ((curr_price - prev_close) / prev_close) * 100

        col1.metric("當前股價", f"${curr_price:,.2f}", f"{price_chg:+.2f}%")
        col2.metric("本益比 (P/E)", info.get('trailingPE', 'N/A'))
        col3.metric("市值", f"{info.get('marketCap', 0)/1e9:,.2f}B")
        col4.metric("52週高點", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")

        # --- B. 股價走勢圖 ---
        st.subheader("📊 價格走勢 (近一年)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Close'], name='收盤價', line=dict(color='#1f77b4')))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=20, b=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # --- C. 功能分頁視窗 ---
        tab1, tab2, tab3 = st.tabs(["💰 殖利率視窗", "🐻 做空監測", "📄 財報視窗"])

        with tab1:
            st.subheader("年利率 (殖利率) 分析")
            divs = fin_data["dividends"]
            if not divs.empty:
                last_year_total = divs.last('365D').sum()
                st.write(f"**過去一年總配息：** ${last_year_total:.2f}")
                st.write(f"**預估殖利率：** {(last_year_total/curr_price)*100:.2f}%")
                st.bar_chart(divs.tail(10))
            else:
                st.info("該標的目前無配息數據。")

        with tab2:
            st.subheader("市場做空與籌碼壓力")
            short_p = info.get('shortPercentOfFloat', 0) * 100
            s_ratio = info.get('shortRatio', "無資料")
            
            c1, c2 = st.columns(2)
            c1.metric("空單佔流通股比", f"{short_p:.2f
