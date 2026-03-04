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
monthly_invest = st.sidebar.number_input("每月定期定額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. Google 新聞抓取函數 ---
def get_google_news(stock_symbol):
    """透過 Google News RSS 抓取即時新聞"""
    # 針對台股與美股調整搜尋關鍵字
    query = f"{stock_symbol} stock news"
    encoded_query = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    
    feed = feedparser.parse(rss_url)
    news_list = []
    for entry in feed.entries[:8]: # 取前 8 則
        news_list.append({
            "title": entry.title,
            "link": entry.link,
            "pub": entry.published
        })
    return news_list

@st.cache_data(ttl=3600)
def fetch_stock_data(tk):
    stock = yf.Ticker(tk)
    return {
        "info": stock.info,
        "hist": stock.history(period="10y")
    }

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('數據同步中...'):
        data = fetch_stock_data(symbol)
        info, hist = data["info"], data["hist"]
        curr_price = info.get('currentPrice') or (hist['Close'].iloc[-1] if not hist.empty else 0)
        google_news = get_google_news(symbol)

    # --- A. 智能診斷燈號 ---
    st.subheader("🤖 AI 診斷報告")
    score = 0
    reasons_pro, reasons_con = [], []

    # 簡單分析邏輯
    pe = info.get('trailingPE')
    if pe and pe < 20:
        score += 1
        reasons_pro.append(f"估值合理 (P/E: {pe:.1f})")
    elif pe:
        reasons_con.append(f"估值偏高 (P/E: {pe:.1f})")

    rev_growth = info.get('revenueGrowth')
    if rev_growth and rev_growth > 0.1:
        score += 1
        reasons_pro.append("營收雙位數成長")

    c1, c2 = st.columns([1, 3])
    with c1:
        if score >= 2: st.success("🟢 健康燈號：表現優異")
        elif score == 1: st.warning("🟡 健康燈號：中性觀察")
        else: st.error("🔴 健康燈號：需警惕")
    with c2:
        st.write(f"**利多分析：** {', '.join(reasons_pro) if reasons_pro else '無'}")
        st.write(f"**利空分析：** {', '.join(reasons_con) if reasons_con else '無'}")

    # --- B. 定期定額回測 ---
    st.divider()
    st.subheader("📅 定期定額回測 (DCA Backtest)")
    if not hist.empty:
        back_df = hist.last(f"{invest_years}Y").copy()
        monthly = back_df.resample('MS').first()
        total_inv = len(monthly) * monthly_invest
        shares = (monthly_invest / monthly['Close']).sum()
        final_val = shares * curr_price
        roi = ((final_val - total_inv) / total_inv) * 100
        
        b1, b2, b3 = st.columns(3)
        b1.metric("總投入本金", f"${total_inv:,.0f}")
        b2.metric("期末資產", f"${final_val:,.0f}")
        b3.metric("報酬率", f"{roi:.2f}%", delta=f"{roi:.2f}%")
        st.line_chart(back_df['Close'])

    # --- C. Google 關鍵新聞 (RSS 來源) ---
    st.divider()
    st.subheader("📰 Google 即時關鍵新聞")
    if google_news:
        # 使用列容器讓新聞排版更美觀
        cols = st.columns(2)
        for i, n in enumerate(google_news):
            with cols[i % 2]:
                st.info(f"📅 {n['pub']}\n\n**[{n['title']}]({n['link']})**")
    else:
        st.write("目前找不到相關 Google 新聞。")

except Exception as e:
    st.error(f"系統異常：{str(e)}")
