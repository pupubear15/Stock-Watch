import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from urllib.parse import quote

# --- 1. 網頁配置 ---
st.set_page_config(page_title="AI 投資智能導航", layout="wide")
st.title("🚀 AI 投資智能導航 (Google News 整合版)")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 股票與回測設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
monthly_invest = st.sidebar.number_input("每月定期定額金額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. 數據處理函數 ---
@st.cache_data(ttl=3600)
def fetch_stock_data(tk):
    stock = yf.Ticker(tk)
    # 抓取 10 年數據以利長線回測
    hist = stock.history(period="10y")
    return {"info": stock.info, "hist": hist}

def get_google_news(stock_symbol):
    """從 Google News RSS 抓取新聞"""
    query = f"{stock_symbol} stock news"
    encoded_query = quote(query)
    # 台灣版 Google News RSS
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(rss_url)
    return feed.entries[:6] # 取前 6 則

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('數據計算中...'):
        data = fetch_stock_data(symbol)
        info, hist = data["info"], data["hist"]
        news_entries = get_google_news(symbol)
        
        # 取得最新股價
        curr_p = info.get('currentPrice') or (hist['Close'].iloc[-1] if not hist.empty else 0)

    # --- A. 智能診斷燈號 & 利多/利空 ---
    st.subheader("🤖 AI 投資健康診斷")
    
    # 評分邏輯 (評分 0~3)
    score = 0
    pro, con = [], []
    
    # 指標 1: 本益比 (P/E)
    pe = info.get('trailingPE')
    if pe:
        if pe < 20: 
            score += 1; pro.append(f"估值偏低 (P/E: {pe:.1f})")
        elif pe > 40: 
            con.append(f"估值過高 (P/E: {pe:.1f})")
            
    # 指標 2: 營收成長
    rev_g = info.get('revenueGrowth')
    if rev_g and rev_g > 0.1:
        score += 1; pro.append(f"營收強勁成長 ({rev_g:.1%})")
        
    # 指標 3: 技術面 (相對於年線)
    ma250 = hist['Close'].rolling(250).mean().iloc[-1]
    if curr_p > ma250:
        score += 1; pro.append("股價位於年線上方 (多頭氣勢)")
    else:
        con.append("股價跌破年線 (空頭整理)")

    # 顯示結果
    col_l1, col_l2 = st.columns([1, 3])
    with col_l1:
        if score >= 2: st.success("🟢 健康燈號：表現優異")
        elif score == 1: st.warning("🟡 健康燈號：中性觀察")
        else: st.error("🔴 健康燈號：需警惕")
    
    with col_l2:
        st.write(f"✅ **利多判斷：** {', '.join(pro) if pro else '無明顯利多'}")
        st.write(f"❌ **利空判斷：** {', '.join(con) if con else '無明顯利空'}")

    # --- B. 資產配置與定期定額回測 ---
    st.divider()
    st.subheader(f"📅 定期定額回測：過去 {invest_years} 年績效")
    
    if not hist.empty:
        # 篩選回測期間數據
        back_df = hist.last(f"{invest_years}Y").copy()
        # 模擬每月 1 號買入 (MS: Month Start)
        monthly_df = back_df.resample('MS').first()
        
        total_inv = len(monthly_df) * monthly_invest
        shares = (monthly_invest / monthly_df['Close']).sum()
        final_val = shares * curr_p
        total_roi = ((final_val - total_inv) / total_inv) * 100
        
        m1, m2, m3 = st.columns(3)
        m1.metric("累積投入本金", f"${total_inv:,.0f}")
        m2.metric("期末資產價值", f"${final_val:,.0f}")
        m3.metric("累積報酬率", f"{total_roi:.2f}%", delta=f"{total_roi:.2f}%")
        
        st.line_chart(back_df['Close'])

    # --- C. Google 關鍵消息與法人籌碼 ---
    st.divider()
    n_col, c_col = st.columns([2, 1])
    
    with n_col:
        st.subheader("📰 Google 即時關鍵新聞")
        for entry in news_entries:
            st.markdown(f"🕒 {entry.published[:16]}")
            st.markdown(f"🔗 **[{entry.title}]({entry.link})**")
            st.write("---")
            
    with c_col:
        st.subheader("👥 法人籌碼監測")
        inst = info.get('heldPercentInstitutions', 0) * 100
        insider = info.get('heldPercentInsiders', 0) * 100
        st.metric("機構持股比例", f"{inst:.2f}%")
        st.write(f"內部持股比例：{insider:.2f}%")
        
        if inst > 50:
            st.info("💡 機構持股過半，籌碼極度集中，適合長期持有。")
        else:
            st.write("💡 機構持股較低，價格波動可能受散戶影響較大。")

except Exception as e:
    st.error(f"系統異常：{str(e)}")
    st.info("提示：台股請加 .TW (如 2330.TW)。")
