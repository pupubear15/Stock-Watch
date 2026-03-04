import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import requests
from urllib.parse import quote

# --- 1. 配置與 Telegram 設定 ---
st.set_page_config(page_title="AI 投資智能導航", layout="wide")

# 請在此填入你的資訊
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
            st.toast("✅ 已成功推送到手機 Telegram！", icon="📱")
        else:
            st.error("❌ 發送失敗，請檢查 Token 與 ID。")
    except Exception as e:
        st.error(f"連線錯誤: {e}")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 股票與回測設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
monthly_invest = st.sidebar.number_input("每月定期定額金額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. 核心功能函數 ---
@st.cache_data(ttl=3600)
def fetch_stock_data(tk):
    stock = yf.Ticker(tk)
    return {"info": stock.info, "hist": stock.history(period="10y")}

def analyze_sentiment(title):
    """新聞情緒分析邏輯"""
    pos = ['新高', '成長', '看旺', '優於預期', '大賺', '噴發', '買進', '上調', '利多', '擴產', '突破']
    neg = ['下滑', '衰退', '裁員', '低於預期', '虧損', '看淡', '下修', '利空', '跌破', '警告', '壓力']
    score = sum(1 for w in pos if w in title) - sum(1 for w in neg if w in title)
    return ("🔴 利多", "red") if score > 0 else (("🟢 利空", "green") if score < 0 else ("⚪ 中立", "gray"))

# --- 4. 主程式邏輯 ---
try:
    with st.spinner('AI 正在同步數據與分析新聞...'):
        data = fetch_stock_data(symbol)
        info, hist = data["info"], data["hist"]
        curr_p = info.get('currentPrice') or (hist['Close'].iloc[-1] if not hist.empty else 0)

    # --- A. 籌碼診斷與 AI 買賣建議 ---
    st.subheader("🤖 AI 籌碼診斷 & 決策建議")
    inst_own = info.get('heldPercentInstitutions', 0) * 100
    short_ratio = info.get('shortPercentOfFloat', 0) * 100
    ma200 = hist['Close'].rolling(200).mean().iloc[-1] # 年線支撐

    decision = "⚖️ 觀望"
    advice_msg = ""
    
    # 決策判斷邏輯
    if inst_own > 50 and curr_p > ma200:
        decision = "🚀 建議買入 (Strong Buy)"
        advice_msg = f"法人持股高 ({inst_own:.1f}%) 且股價高於年線，趨勢強勁。"
        st.success(decision)
    elif short_ratio > 15 or curr_p < ma200:
        decision = "⚠️ 警惕/減碼 (Warning)"
        advice_msg = f"空單比例高 ({short_ratio:.1f}%) 或股價跌破年線，籌碼出現鬆動。"
        st.error(decision)
    else:
        decision = "⚖️ 中性持股 (Hold)"
        advice_msg = "目前籌碼與趨勢處於震盪整理區。"
        st.
    
