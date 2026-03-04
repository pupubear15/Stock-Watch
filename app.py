import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import requests
from urllib.parse import quote

# --- 1. 配置與 Telegram 設定 ---
st.set_page_config(page_title="AI 投資導航", layout="wide")

# 請填入你的資訊 (LINE Notify 已停用，改用 Telegram)
TG_TOKEN = "你的_TELEGRAM_BOT_TOKEN"
TG_CHAT_ID = "你的_CHAT_ID"

def send_tg_msg(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        st.toast("✅ 已推送到 Telegram！", icon="📱")
    except: st.error("❌ 發送失敗")

# --- 2. 側邊欄 ---
st.sidebar.header("🔍 監測設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
m_inv = st.sidebar.number_input("每月投入 ($)", value=1000)
years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. 分析函數 ---
@st.cache_data(ttl=3600)
def get_data(tk):
    stock = yf.Ticker(tk)
    return {"info": stock.info, "hist": stock.history(period="10y")}

def get_sentiment(title):
    pos = ['新高', '成長', '看旺', '優於預期', '利多', '擴產', '突破']
    neg = ['下滑', '衰退', '裁員', '低於預期', '利空', '警告', '壓力']
    score = sum(1 for w in pos if w in title) - sum(1 for w in neg if w in title)
    return "🔴 利多" if score > 0 else ("🟢 利利" if score < 0 else "⚪ 中立")

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('數據同步中...'):
        data = get_data(symbol)
        info, hist = data["info"], data["hist"]
        curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]

    # --- A. 籌碼診斷 ---
    st.subheader("🤖 AI 籌碼診斷 & 決策")
    inst = info.get('heldPercentInstitutions', 0) * 100
    short = info.get('shortPercentOfFloat', 0) * 100
    ma200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) > 200 else curr_p

    if inst > 50 and curr_p > ma200:
        decision, note = "🚀 建議買入", "法人高度持股且站穩年線。"
        st.success(decision)
    elif short > 10 or curr_p < ma200:
        decision, note = "⚠️ 警惕減碼", "空單過高或跌破年線支撐。"
        st.error(decision)
    else:
        decision, note = "⚖️ 中性觀望", "目前處於盤整區間。"
        st.info(decision)

    if st.button(f"📲 推送 {symbol} 決策"):
        send_tg_msg(f"*【AI 投資通知】*\n📍 標的: {symbol}\n💰 現價: {curr_p:.2f}\n📢 決策: {decision}\n📝 原因: {note}")

    # --- B. 定期定額回測 ---
    st.divider()
    if not hist.empty:
        st.subheader(f"📅 過去 {years} 年定期定額回測")
        b_df = hist.last(f"{years}Y").copy()
        m_df = b_df.resample('MS').first()
        t_inv = len(m_df) * m_inv
        shares = (m_inv / m_df['Close']).sum()
        f_val = shares * curr_p
        roi = ((f_val - t_inv) / t_inv) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.metric("投入本金", f"${t_inv:,.0f}")
        c2.metric("期末資產", f"${f_val:,.0f}")
        c3.metric("累積報酬率", f"{roi:.2f}%", delta=f"{roi:.2f}%")
        st.line_chart(b_df['Close'])
        

    # --- C. Google 新聞情緒 ---
    st.divider()
    st.subheader("📰 即時新聞情緒分析")
    q = quote(f"{symbol} 股票")
    url = f"https://news.google.com/rss/search?q={q}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    news = feedparser.parse(url).entries[:5]
    for n in news:
        st.write(f"**{get_sentiment(n.title)}** | [{n.title}]({n.link})")

except Exception as e:
    st.error(f"錯誤: {e}")
