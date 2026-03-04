import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
from urllib.parse import quote

# --- 1. 網頁配置 ---
st.set_page_config(page_title="AI 投資智能導航", layout="wide")
st.title("🚀 AI 投資智能導航 (即時新聞情緒分析版)")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 股票與回測設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
monthly_invest = st.sidebar.number_input("每月定期定額金額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. AI 情緒分析函數 ---
def analyze_sentiment(title):
    """
    簡單高效的財經情緒分析邏輯
    """
    pos_words = ['新高', '增長', '看旺', '優於預期', '大賺', '噴發', '買進', '上調', '利多', '成長', '擴產', '突破']
    neg_words = ['下滑', '衰退', '裁員', '低於預期', '虧損', '看淡', '下修', '利空', '跌破', '警告', '保守', '壓力']
    
    score = 0
    for word in pos_words:
        if word in title: score += 1
    for word in neg_words:
        if word in title: score -= 1
        
    if score > 0: return "🔴 利多", "inverse_surface"
    elif score < 0: return "🟢 利空", "normal" # 財經傳統：紅漲綠跌
    else: return "⚪ 中立", "off"

def get_google_news(stock_symbol):
    query = f"{stock_symbol} 股票 新聞"
    encoded_query = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(rss_url)
    return feed.entries[:8]

# --- 4. 數據抓取 ---
@st.cache_data(ttl=3600)
def fetch_data(tk):
    stock = yf.Ticker(tk)
    return {"info": stock.info, "hist": stock.history(period="10y")}

# --- 5. 主程式邏輯 ---
try:
    with st.spinner('AI 正在讀取並分析新聞情緒...'):
        data = fetch_data(symbol)
        info, hist = data["info"], data["hist"]
        news_entries = get_google_news(symbol)
        curr_p = info.get('currentPrice') or (hist['Close'].iloc[-1] if not hist.empty else 0)

    # --- A. AI 診斷與利多利空 ---
    st.subheader("🤖 AI 投資診斷")
    col_a, col_b = st.columns([1, 2])
    
    # 這裡保留原本的數據診斷邏輯
    rev_g = info.get('revenueGrowth', 0)
    pe = info.get('trailingPE', 0)
    
    with col_a:
        if rev_g > 0.1 and pe < 30:
            st.success("🎯 綜合評價：建議關注 (多頭)")
        else:
            st.warning("⚖️ 綜合評價：中性/保守")

    # --- B. 即時新聞情緒分析 (核心功能) ---
    st.divider()
    st.subheader("📰 即時新聞與 AI 情緒標籤")
    
    if news_entries:
        for entry in news_entries:
            sentiment_tag, style = analyze_sentiment(entry.title)
            
            with st.expander(f"{sentiment_tag} | {entry.title[:50]}..."):
                st.write(f"**完整標題：** {entry.title}")
                st.write(f"**發布時間：** {entry.published}")
                st.markdown(f"🔗 [點擊閱讀全文]({entry.link})")
                
                if "利多" in sentiment_tag:
                    st.toast(f"發現利多消息: {symbol}", icon="📈")
    else:
        st.write("暫無相關新聞。")

    # --- C. 定期定額回測 ---
    st.divider()
    st.subheader(f"📅 定期定額回測 (過去 {invest_years} 年)")
    if not hist.empty:
        back_df = hist.last(f"{invest_years}Y").copy()
        monthly = back_df.
