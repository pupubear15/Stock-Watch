import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
from urllib.parse import quote

# --- 1. 網頁配置 ---
st.set_page_config(page_title="AI 投資智能導航", layout="wide")
st.title("🚀 AI 投資智能導航 (新聞情緒分析版)")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 股票與回測設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
monthly_invest = st.sidebar.number_input("每月定期定額金額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. 核心功能函數 ---
def analyze_news_sentiment(title):
    """分析財經新聞情緒：回傳 (標籤, 顏色)"""
    # 定義關鍵字庫
    pos = ['新高', '成長', '看旺', '優於預期', '大賺', '噴發', '買進', '上調', '利多', '擴產', '突破', '轉盈']
    neg = ['下滑', '衰退', '裁員', '低於預期', '虧損', '看淡', '下修', '利空', '跌破', '警告', '保守', '壓力']
    
    score = 0
    for word in pos:
        if word in title: score += 1
    for word in neg:
        if word in title: score -= 1
        
    if score > 0: return "🔴 利多", "red"  # 財經習慣：紅漲
    elif score < 0: return "🟢 利空", "green" # 財經習慣：綠跌
    return "⚪ 中立", "gray"

@st.cache_data(ttl=3600)
def fetch_stock_data(tk):
    stock = yf.Ticker(tk)
    return {"info": stock.info, "hist": stock.history(period="10y")}

def get_google_news(tk):
    query = quote(f"{tk} 股票新聞")
    url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    return feed.entries[:8]

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('AI 正在同步數據與分析新聞...'):
        data = fetch_stock_data(symbol)
        info, hist = data["info"], data["hist"]
        news_list = get_google_news(symbol)
        curr_p = info.get('currentPrice') or (hist['Close'].iloc[-1] if not hist.empty else 0)

    # --- A. AI 診斷與利多/利空判斷 ---
    st.subheader("🤖 AI 投資健康診斷")
    score = 0
    pro, con = [], []
    
    # 簡易診斷邏輯
    pe = info.get('trailingPE')
    if pe and pe < 20:
        score += 1; pro.append(f"估值合理 (P/E: {pe:.1f})")
    elif pe and pe > 40:
        con.append(f"估值過高 (P/E: {pe:.1f})")

    rev_g = info.get('revenueGrowth', 0)
    if rev_g and rev_g > 0.1:
        score += 1; pro.append(f"營收成長強勁 ({rev_g:.1%})")

    l1, l2 = st.columns([1, 3])
    with l1:
        if score >= 2: st.success("🟢 健康燈號：表現優異")
        elif score == 1: st.warning("🟡 健康燈號：中性觀察")
        else: st.error("🔴 健康燈號：需警惕")
    with l2:
        st.write(f"✅ **利多分析：** {', '.join(pro) if pro else '無'}")
        st.write(f"❌ **利空分析：** {', '.join(con) if con else '無'}")

    # --- B. 定期定額回測 ---
    st.divider()
    st.subheader(f"📅 定期定額回測分析 (過去 {invest_years} 年)")
    if not hist.empty:
        # 篩選歷史數據
        back_df = hist.last(f"{invest_years}Y").copy()
        # 模擬每月1號投入
        monthly_df = back_df.resample('MS').first()
        
        total_inv = len(monthly_df) * monthly_invest
        shares = (monthly_invest / monthly_df['Close']).sum()
        final_val = shares * curr_p
        roi = ((final_val - total_inv) / total_inv) * 100
        
        m1, m2, m3 = st.columns(3)
        m1.metric("累積投入本金", f"${total_inv:,.0f}")
        m2.metric("期末資產價值", f"${final_val:,.0f}")
        m3.metric("累積報酬率", f"{roi:.2f}%", delta=f"{roi:.2f}%")
        st.line_chart(back_df['Close'])

    # --- C. Google 即時新聞與情緒分析 ---
    st.divider()
    st.subheader("📰 Google 即時關鍵新聞 (AI 情緒偵測)")
    
    if news_list:
        for entry in news_list:
            tag, color = analyze_news_sentiment(entry.title)
            with st.expander(f"{tag} | {entry.title[:60]}..."):
                st.write(f"**完整標題：** {entry.title}")
                st.write(f"**發布時間：** {entry.published}")
                st.markdown(f"🔗 [點擊開啟 Google 新聞連結]({entry.link})")
                if tag == "🔴 利多":
                    st.toast(f"發現利多訊息: {symbol}", icon="🔥")
    else:
        st.info("目前無相關 Google 新聞。")

except Exception as e:
    st.error(f"系統運行異常：{str(e)}")
    st.info("💡 提示：輸入代號如 AAPL (美股) 或 2330.TW (台股)。")
