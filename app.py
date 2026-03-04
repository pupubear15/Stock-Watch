import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import requests
from urllib.parse import quote

# --- 1. 配置與 Telegram 設定 ---
st.set_page_config(page_title="AI 投資智能導航", layout="wide")

# 請在此填入你的 Telegram Bot 資訊
TG_TOKEN = "你的_TELEGRAM_BOT_TOKEN"
TG_CHAT_ID = "你的_CHAT_ID"

def send_telegram_msg(message):
    """發送 Telegram 通知函數"""
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
        st.error(f"Telegram 連線錯誤: {e}")

# --- 2. 側邊欄設定 ---
st.sidebar.header("🔍 股票與回測設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
monthly_invest = st.sidebar.number_input("每月定期定額金額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. 核心分析函數 ---
@st.cache_data(ttl=3600)
def fetch_stock_data(tk):
    stock = yf.Ticker(tk)
    # 抓取較長歷史數據以利回測
    hist = stock.history(period="10y")
    return {"info": stock.info, "hist": hist}

def analyze_sentiment(title):
    """即時新聞情緒掃描邏輯"""
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
    # 計算 200 日均線 (年線)
    ma200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else curr_p

    decision = "⚖️ 觀望"
    advice_msg = ""
    
    # 核心決策判斷
    if inst_own > 50 and curr_p > ma200:
        decision = "🚀 建議買入 (Strong Buy)"
        advice_msg = f"法人持股高 ({inst_own:.1f}%) 且股價站穩年線以上，具備長線支撐。"
        st.success(decision)
    elif short_ratio > 10 or curr_p < ma200:
        decision = "⚠️ 警惕/減碼 (Warning)"
        advice_msg = f"空單佔比偏高 ({short_ratio:.1f}%) 或股價跌破年線，籌碼結構不穩。"
        st.error(decision)
    else:
        decision = "⚖️ 中性持股 (Hold)"
        advice_msg = "目前籌碼面與趨勢面處於平衡狀態，無明顯買賣點。"
        st.info(decision)

    # 推送按鈕
    if st.button(f"📲 推送 {symbol} 決策至手機"):
        msg = f"*【AI 投資決策通知】*\n\n" \
              f"📍 *標的：* {symbol}\n" \
              f"💰 *現價：* {curr_p:,.2f}\n" \
              f"📢 *決策：* {decision}\n" \
              f"📝 *理由：* {advice_msg}"
        send_telegram_msg(msg)

    # --- B. 定期定額回測 ---
    st.divider()
    st.subheader(f"📅 定期定額回測績效 (過去 {invest_years} 年)")
    if not hist.empty:
        back_df = hist.last(f"{invest_years}Y").copy()
        # 模擬每月 1 號投入
        monthly_df = back_df.resample('MS').first()
        total_
