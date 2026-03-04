import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 網頁配置 ---
st.set_page_config(page_title="投資新手監測站", layout="wide")

st.title("📈 投資新手全方位監測儀表板")
st.caption("數據來源：Yahoo Finance | 修正：F-string 語法與序列化錯誤")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 股票查詢")
ticker_symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()

# --- 3. 數據抓取函數 (分離物件以利快取) ---
@st.cache_data(ttl=3600)
def fetch_basic_data(symbol):
    stock = yf.Ticker(symbol)
    # 只回傳基礎類型與 DataFrame
    return stock.info, stock.history(period="1y")

@st.cache_data(ttl=3600)
def fetch_financial_data(symbol):
    stock = yf.Ticker(symbol)
    # 回傳純數據字典
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
        
        # 安全取值邏輯
        curr_p = info.get('currentPrice') or (hist_data['Close'].iloc[-1] if not hist_data.empty else 0)
        prev_p = info.get('previousClose') or (hist_data['Close'].iloc[0] if not hist_data.empty else 1)
        chg_pct = ((curr_p - prev_p) / prev_p) * 100

        col1.metric("當前股價", f"${curr_p:,.2f}", f"{chg_pct:+.2f}%")
        col2.metric("本益比 (P/E)", info.get('trailingPE', 'N/A'))
        col3.metric("市值", f"{info.get('marketCap', 0)/1e9:,.1f}B")
        col4.metric("52週高點", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")

        # --- B. 股價走勢圖 ---
        st.subheader("📊 價格走勢 (近一年)")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['Close'], name='收盤價', line=dict(color='#1f77b4')))
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # --- C. 三大功能分頁 ---
        tab1, tab2, tab3 = st.tabs(["💰 殖利率視窗", "🐻 做空監測", "📄 財報視窗"])

        with tab1:
            st.subheader("年利率 (殖利率) 分析")
            divs = fin_data["divs"]
            if not divs.empty:
                total_1y = divs.last('365D').sum()
                y_rate = (total_1y / curr_p) * 100 if curr_p > 0 else 0
                st.write(f"**過去一年總配息：** ${total_1y:.2f}")
                st.write(f"**預估殖利率：** {y_rate:.2f}%")
                st.bar_chart(divs.tail(10))
            else:
                st.info("暫無配息數據。")

        with tab2:
            st.subheader("市場空方情緒")
            # 確保數值計算正確且不換行
            short_p = info.get('shortPercentOfFloat', 0) * 100
            s_ratio = info.get('shortRatio', "N/A")
            
            sc1, sc2 = st.columns(2)
            sc1.metric("空單佔流通股比", f"{short_p:.2f}%")
            sc2.metric("空單回補天數", f"{s_ratio}")
            
            if short_p > 10:
                st.warning("⚠️ 警告：空方比例顯著，代表市場看跌情緒較重。")
            else:
                st.success("✅ 目前籌碼面相對穩定，無明顯空方聚集。")

        with tab3:
            st.subheader("年度財務報表")
            r_type = st.radio("選擇
