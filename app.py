import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 網頁基礎配置 ---
st.set_page_config(page_title="AI 投資新手監測站", layout="wide", initial_sidebar_state="expanded")

# 自定義 CSS 讓介面更美觀
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 全方位投資監測儀表板")
st.caption("數據來源：Yahoo Finance | 開發架構：Streamlit + GitHub")

# --- 側邊欄設定 ---
st.sidebar.header("🔍 股票查詢")
ticker_symbol = st.sidebar.text_input("請輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
time_window = st.sidebar.selectbox("觀看區間", ["1y", "2y", "5y", "max"], index=0)

# --- 數據抓取函數 (加上快取機制以提升速度) ---
@st.cache_data(ttl=3600)
def fetch_data(symbol):
    stock = yf.Ticker(symbol)
    # 抓取歷史價格
    hist = stock.history(period=time_window)
    # 抓取基本面資訊
    info = stock.info
    return stock, hist, info

# --- 主程式邏輯 ---
try:
    with st.spinner('數據讀取中...'):
        stock_obj, hist_data, info = fetch_data(ticker_symbol)

    if hist_data.empty:
        st.error("找不到該股票數據，請檢查代號是否正確（例如台股需加 .TW）。")
    else:
        # --- 1. 頂部核心指標 ---
        col1, col2, col3, col4 = st.columns(4)
        
        # 處理可能的缺失數值
        curr_price = info.get('currentPrice') or hist_data['Close'].iloc[-1]
        prev_close = info.get('previousClose') or hist_data['Close'].iloc[0]
        price_chg = ((curr_price - prev_close) / prev_close) * 100
        
        col1.metric("當前股價", f"${curr_price:,.2f}", f"{price_chg:+.2f}%")
        col2.metric("市值 (Market Cap)", f"{info.get('marketCap', 0)/1e9:,.2f}B")
        col3.metric("本益比 (P/E)", f"{info.get('trailingPE', 'N/A')}")
        col4.metric("52週高點", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")

        # --- 2. 股價走勢圖 ---
        st.subheader("📊 價格走勢與移動平均線")
        hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
        hist_data['MA60'] = hist_data['Close'].rolling(window=60).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Close'], name='收盤價', line=dict(color='#1f77b4', width=2)))
        fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA20'], name='月線 (MA20)', line=dict(color='#ff7f0e', dash='dot')))
        fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA60'], name='季線 (MA60)', line=dict(color='#2ca02c', dash='dash')))
        fig.update_layout(hovermode="x unified", margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

        # --- 3. 功能分頁視窗 ---
        tab_div, tab_short, tab_finance = st.tabs(["💰 殖利率視窗", "🐻 做空監測", "📄 財報視窗"])

        # --- 殖利率視窗 ---
        with tab_div:
            st.subheader("股利與年利率分析")
            divs = stock_obj.dividends
            if not divs.empty:
                # 計算過去一年的殖利率
                total_div_1y = divs.last('365D').sum()
                yield_val = (total_div_1y / curr_price) * 100
                
                c1, c2 = st.columns([1, 2])
                c1.metric("預估年化殖利率", f"{yield_val:.2f}%")
                c1.write(f"過去 12 個月總配息: ${total_div_1y:.2f}")
                c2.write("近期配息歷史：")
                c2.bar_chart(divs.tail(8))
            else:
                st.info("此標的目前無配息數據（可能是成長股或代號無連動）。")

        # --- 做空監測視窗 ---
        with tab_short:
            st.subheader("市場空方情緒指標")
            # 抓取做空相關指標
            short_ratio = info.get('shortRatio', "無資料")
            short_float = info.get('shortPercentOfFloat', 0) * 100
            
            s_col1, s_col2 = st.columns(2)
            s_col1.metric("空單佔流通股比", f"{short_float:.2f}%")
            s_col2.metric("空單回補天數 (Days to Cover)", short_ratio)

            st.write("---")
            if short_float > 15:
                st.error("⚠️ 高風險警告：該股目前被大量放空，股價波動可能劇烈。")
            elif short_float > 7:
                st.warning("⚡ 注意：空方勢力抬頭，建議觀察是否有負面消息。")
            else:
                st.success("🍀 提示：目前空方壓力較低，籌碼面相對平穩。")

        # --- 財報視窗 ---
        with tab_finance:
            st.subheader("公司財務報表 (年度)")
            f_type = st.selectbox("請選擇報表類型", ["損益表 (Income Statement)", "資產負債表 (Balance Sheet)", "現金流量表 (Cash Flow)"])
            
            if "損益表" in f_type:
                df = stock_obj.financials
            elif "資產負債表" in f_type:
                df = stock_obj.balance_sheet
            else:
                df = stock_obj.cashflow

            if df is not None and not df.empty:
                st.dataframe(df.style.format(precision=2), use_container_width=True)
                
                # 財報視覺化範例：營收趨勢
                if "Total Revenue" in df.index:
                    st.write("**總營收趨勢變化：**")
                    st.line_chart(df.loc["Total Revenue"])
            else:
                st.info("暫無可用的財報數據，請稍後再試。")

except Exception as e:
    st.error(f"⚠️ 啟動失敗：{e}")
    st.info("建議嘗試：1. 檢查代號 (台股如 2330.TW) 2. 稍後重新整理頁面。")
