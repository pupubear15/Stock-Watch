import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 網頁配置 ---
st.set_page_config(page_title="投資新手監測站", layout="wide")

st.title("📈 投資新手全方位監測儀表板")
st.caption("數據來源：Yahoo Finance | 版本：V1.3 (修復字串閉合錯誤)")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 股票查詢")
ticker_symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()

# --- 3. 數據抓取函數 (分離物件以利快取) ---
@st.cache_data(ttl=3600)
def fetch_basic_data(symbol):
    stock = yf.Ticker(symbol)
    return stock.info, stock.history(period="1y")

@st.cache_data(ttl=3600)
def fetch_financial_data(symbol):
    stock = yf.Ticker(symbol)
    return {
        "divs": stock.dividends,
        "income": stock.financials,
        "balance": stock.balance_sheet,
        "cashflow": stock.cashflow
    }

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('數據讀取中...'):
        info, hist_data = fetch_basic_data(ticker_symbol)
        fin_data = fetch_financial_data(ticker_symbol)

    if hist_data.empty:
        st.error("找不到該股票數據，請檢查代號（台股需加 .TW）。")
    else:
        # --- A. 核心指標卡片 ---
        col1, col2, col3, col4 = st.columns(4)
        
        curr_p = info.get('currentPrice') or (hist_data['Close'].iloc[-1] if not hist_data.empty else 0)
        prev_p = info.get('previousClose') or (hist_data['Close'].iloc[0] if not hist_data.empty else 1)
        chg_pct = ((curr_p - prev_p) / prev_p) * 100

        col1.metric("當前股價", f"${curr_p:,.2f}", f"{chg_pct:+.2f}%")
        col2.metric("本益比 (P/E)", info.get('trailingPE', 'N/A'))
        col3.metric("市值", f"{info.get('marketCap', 0)/1e
