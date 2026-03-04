import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import requests
from urllib.parse import quote

# --- 1. 配置 Telegram 設定 ---
st.set_page_config(page_title="AI 投資決策系統", layout="wide")

# 這裡請輸入你的 Token 和 Chat ID
TG_TOKEN = "你的_TELEGRAM_BOT_TOKEN"
TG_CHAT_ID = "你的_CHAT_ID"

def send_telegram_msg(message):
    """發送 Telegram 通知"""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            st.toast("✅ 手機 Telegram 通知發送成功！", icon="📱")
        else:
            st.error("❌ 發送失敗，請檢查 Token 與 Chat ID。")
    except Exception as e:
        st.error(f"Telegram 連線錯誤: {e}")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 決策參數設定")
symbol = st.sidebar.text_input("輸入代號", "AAPL").upper()
auto_diag = st.sidebar.checkbox("開啟 AI 籌碼診斷", value=True)

# --- 3. 數據抓取 ---
@st.cache_data(ttl=3600)
def fetch_stock_data(tk):
    stock = yf.Ticker(tk)
    return {"info": stock.info, "hist": stock.history(period="1y")}

def analyze_sentiment(title):
    pos = ['新高', '成長', '看旺', '優於預期', '大賺', '噴發', '買進', '上調', '利多', '擴產', '突破']
    neg = ['下滑', '衰退', '裁員', '低於預期', '虧損', '看淡', '下修', '利空', '跌破', '警告', '壓力']
    score = sum(1 for w in pos if w in title) - sum(1 for w in neg if w in title)
    return ("🔴 利多", "red") if score > 0 else (("🟢 利空", "green") if score < 0 else ("⚪ 中立", "gray"))

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('正在分析籌碼與即時新聞...'):
        data = fetch_stock_data(symbol)
        info, hist = data["info"], data["hist"]
        curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]

    # --- A. 籌碼面數據顯示 ---
    st.subheader("👥 法人籌碼監測")
    c1, c2, c3 = st.columns(3)
    inst_own = info.get('heldPercentInstitutions', 0) * 100
    insider_own = info.get('heldPercentInsiders', 0) * 100
    short_ratio = info.get('shortPercentOfFloat', 0) * 100
    
    c1.metric("機構持股比例", f"{inst_own:.2f}%")
    c2.metric("內部人持股比例", f"{insider_own:.2f}%")
    c3.metric("空單佔比 (Short)", f"{short_ratio:.2f}%")

    # --- B. AI 買賣決策與通知 ---
    st.divider()
    st.subheader("🤖 AI 即時買賣建議")
    
    decision = "⚖️ 觀望"
    advice_msg = ""
    color = "info"

    # 決策邏輯
    if inst_own > 50 and curr_p > hist['Close'].rolling(200).mean().iloc[-1]:
        decision = "🚀 建議買入 (Strong Buy)"
        advice_msg = f"法人持股高達 {inst_own:.1f}%，且股價站穩年線，呈現多頭排列。"
        st.success(decision)
    elif short_ratio > 15 or curr_p < hist['Close'].rolling(200).mean().iloc[-1]:
        decision = "⚠️ 建議賣出/保守 (Sell/Warning)"
        advice_msg = f"空單比例偏高 ({short_ratio:.1f}%) 或股價跌破年線，籌碼面出現鬆動。"
        st.error(decision)
    else:
        decision = "⚖️ 中性持股 (Hold)"
        advice_msg = "籌碼與趨勢處於震盪區間，建議等待明顯突破訊號。"
        st.info(decision)

    st.write(f"**詳細診斷：** {advice_msg}")

    # 發送 Telegram 按鈕
    if st.button(f"📲 推送決策至手機 (Telegram)"):
        tg_text = f"*【AI 投資決策通知】*\n\n" \
                  f"📍 *標的：* {symbol}\n" \
                  f"💰 *現價：* {curr_p:.2f}\n" \
                  f"📢 *決策：* {decision}\n" \
                  f"📝 *原因：* {advice_msg}"
        send_telegram_msg(tg_text)

    # --- C. Google 新聞情緒分析 ---
    st.divider()
    st.subheader("📰 Google 即時新聞情緒分析")
    query = quote(f"{symbol} 股票新聞")
    url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    news_feed = feedparser.parse(url).entries[:6]
    
    for n in news_feed:
        tag, tag_col = analyze_sentiment(n.title)
        st.markdown(f"**{tag}** | [{n.title}]({n.link})")

except Exception as e:
    st.error(f"系統異常：{str(e)}")
