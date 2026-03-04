import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- 1. 網頁配置 ---
st.set_page_config(page_title="AI 投資智能導航", layout="wide")
st.title("🚀 AI 投資智能導航 & 決策系統")

# --- 2. 側邊欄：輸入與回測參數 ---
st.sidebar.header("🔍 股票與回測設定")
symbol = st.sidebar.text_input("輸入代號", "AAPL").upper()
monthly_invest = st.sidebar.number_input("每月定期定額金額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. 數據抓取函數 ---
@st.cache_data(ttl=3600)
def fetch_all_data(tk):
    stock = yf.Ticker(tk)
    return {
        "info": stock.info,
        "hist": stock.history(period="10y"), # 為了回測抓長一點
        "income": stock.financials,
        "news": stock.news[:5]
    }

try:
    with st.spinner('AI 正在分析數據...'):
        d = fetch_all_data(symbol)
        info, hist = d["info"], d["hist"]
        curr_price = info.get('currentPrice') or hist['Close'].iloc[-1]

    # --- A. 智能健康燈號 & 利多利空 ---
    st.subheader("🤖 AI 診斷報告")
    score = 0
    reasons_pro = []
    reasons_con = []

    # 邏輯判斷
    pe = info.get('trailingPE', 100)
    if pe < 20: 
        score += 1
        reasons_pro.append("本益比偏低，價值顯現")
    else:
        reasons_con.append("本益比偏高，估值需注意")

    short_pct = info.get('shortPercentOfFloat', 0)
    if short_pct < 0.05:
        score += 1
        reasons_pro.append("空方勢力極小，籌碼穩定")
    else:
        reasons_con.append("空單比例較高，市場看空情緒濃")

    rev_growth = info.get('revenueGrowth', 0)
    if rev_growth > 0.1:
        score += 1
        reasons_pro.append("營收雙位數成長，動力強勁")

    # 燈號顯示
    l1, l2 = st.columns([1, 3])
    with l1:
        if score >= 2:
            st.success("🟢 健康燈號：表現優異")
            signal = "🐂 利多趨勢"
        elif score == 1:
            st.warning("🟡 健康燈號：中性觀察")
            signal = "📉 震盪整理"
        else:
            st.error("🔴 健康燈號：需警惕")
            signal = "🐻 利空壓制"
    
    with l2:
        st.write(f"**當前判定：{signal}**")
        st.write(f"✅ 利多因素：{', '.join(reasons_pro) if reasons_pro else '無'}")
        st.write(f"❌ 利空因素：{', '.join(reasons_con) if reasons_con else '無'}")

    # --- B. 定期定額回測 ---
    st.divider()
    st.subheader("📅 定期定額實測 (Backtesting)")
    backtest_data = hist.last(f"{invest_years}Y").copy()
    # 簡化回測：每月第一天買入
    monthly_data = backtest_data.resample('MS').first()
    total_shares = 0
    total_invested = 0
    for price in monthly_data['Close']:
        total_shares += monthly_invest / price
        total_invested += monthly_invest
    
    current_value = total_shares * curr_price
    roi = ((current_value - total_invested) / total_invested) * 100
    
    b1, b2, b3 = st.columns(3)
    b1.metric("累積投入本金", f"${total_invested:,.0f}")
    b2.metric("當前資產價值", f"${current_value:,.0f}")
    b3.metric("累積報酬率", f"{roi:.2f}%", delta=f"{roi:.2f}%")

    # --- C. 關鍵消息與法人籌碼 ---
    st.divider()
    m1, m2 = st.columns(2)
    
    with m1:
        st.subheader("📰 關鍵新聞")
        for n in d["news"]:
            st.write(f"🔗 [{n['title']}]({n['link']})")
    
    with m2:
        st.subheader("👥 法人與機構籌碼")
        inst_own = info.get('heldPercentInstitutions', 0) * 100
        insider_own = info.get('heldPercentInsiders', 0) * 100
        st.write(f"**機構持股比例：** {inst_own:.2f}%")
        st.write(f"**內部人持股比例：** {insider_own:.2f}%")
        # 籌碼診斷
        if inst_own > 50:
            st.info("💡 機構法人高度控盤，股價較具支撐。")
        else:
            st.write("💡 散戶比例較高，波動可能較大。")

    # --- D. 走勢圖 ---
    st.subheader("📈 歷史價格走勢")
    st.line_chart(backtest_data['Close'])

except Exception as e:
    st.error(f"系統異常：{e}")
    st.info("請確認代號輸入正確（台股請加 .TW）。")
