import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 網頁配置
st.set_page_config(page_title="AI 投資新手監測站", layout="wide")

st.title("📈 投資新手全方位監測儀表板")
st.markdown("利用 GitHub 與 Streamlit 打造的自動化分析工具")

# --- 側邊欄：輸入設定 ---
st.sidebar.header("查詢設定")
ticker_input = st.sidebar.text_input("請輸入股票代號 (美股如 AAPL, 台股如 2330.TW)", "AAPL")
period = st.sidebar.selectbox("資料時間範圍", ["1y", "2y", "5y", "max"])

@st.cache_data(ttl=3600)
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    hist = stock.history(period=period)
    info = stock.info
    return stock, hist, info

try:
    stock_obj, hist_data, info = get_stock_data(ticker_input)
    
    # --- 1. 核心指標卡片 ---
    col1, col2, col3, col4 = st.columns(4)
    current_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
    prev_close = info.get('previousClose', hist_data['Close'].iloc[-2])
    price_diff = ((current_price - prev_close) / prev_close) * 100

    col1.metric("當前股價", f"${current_price:.2f}", f"{price_diff:.2f}%")
    col2.metric("市值", f"{info.get('marketCap', 0)/1e9:.2f}B USD")
    col3.metric("本益比 (P/E)", f"{info.get('trailingPE', 'N/A')}")
    col4.metric("52週高點", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")

    # --- 2. 股價與技術分析 ---
    st.subheader("📊 股價走勢與均線")
    hist_data['MA20'] = hist_data['Close'].rolling(window=20).mean()
    hist_data['MA60'] = hist_data['Close'].rolling(window=60).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Close'], name='收盤價', line=dict(color='royalblue')))
    fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA20'], name='月線 (MA20)', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA60'], name='季線 (MA60)', line=dict(dash='dash')))
    st.plotly_chart(fig, use_container_width=True)

    # --- 3. 殖利率、做空、財報分頁 ---
    tab1, tab2, tab3 = st.tabs(["💰 殖利率與配息", "🐻 做空壓力監測", "📄 財務報表"])

    with tab1:
        st.subheader("年化殖利率分析")
        dividends = stock_obj.dividends
        if not dividends.empty:
            last_year_div = dividends.last('365D').sum()
            yield_rate = (last_year_div / current_price) * 100
            st.write(f"**過去一年總配息：** ${last_year_div:.2f}")
            st.write(f"**預估現金殖利率：** {yield_rate:.2f}%")
            st.bar_chart(dividends.tail(10))
        else:
            st.info("該標的近期無配息紀錄。")

    with tab2:
        st.subheader("空方勢力診斷")
        # 獲取空單數據
        short_ratio = info.get('shortRatio', 0)
        short_percent = info.get('shortPercentOfFloat', 0) * 100
        
        c1, c2 = st.columns(2)
        c1.write(f"**空單佔在外流通股數比 (Short % of Float):** {short_percent:.2f}%")
        c2.write(f"**空單回補天數 (Days to Cover):** {short_ratio} 天")

        # 邏輯判斷
        if short_percent > 15:
            st.error("⚠️ 警告：空單比例極高，可能存在暴跌風險或潛在的「軋空」機會。")
        elif short_percent > 5:
            st.warning("⚡ 注意：市場空方情緒增加，波動可能加劇。")
        else:
            st.success("✅ 目前空方壓力較低，籌碼面相對穩定。")

    with tab3:
        st.subheader("三大財報數據")
        statement_type = st.radio("選擇報表類型", ["損益表", "資產負債表", "現金流量表"], horizontal=True)
        
        if statement_type == "損益表":
            df = stock_obj.financials
        elif statement_type == "資產負債表":
            df = stock_obj.balance_sheet
        else:
            df = stock_obj.cashflow
        
        if not df.empty:
            st.dataframe(df.style.highlight_max(axis=1, color='#2E7D32'))
            # 簡易圖表顯示營收
            if "Total Revenue" in df.index:
                st.write("**總營收趨勢 (按年):**")
                st.line_chart(df.loc["Total Revenue"])
        else:
            st.info("無法獲取對應的財報數據。")

except Exception as e:
    st.error(f"發生錯誤：{e}。請檢查代號是否輸入正確（台股請加 .TW）。")

# --- 頁尾 ---
st.divider()
st.caption("數據來源：Yahoo Finance | 開發工具：Streamlit & GitHub")
