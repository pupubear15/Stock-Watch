import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. 網頁配置 ---
st.set_page_config(page_title="AI 投資智能導航", layout="wide")
st.title("🚀 AI 投資智能導航 & 決策系統")

# --- 2. 側邊欄：輸入與參數 ---
st.sidebar.header("🔍 股票與回測設定")
symbol = st.sidebar.text_input("輸入代號 (如: AAPL, 2330.TW)", "AAPL").upper()
monthly_invest = st.sidebar.number_input("每月定期定額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

# --- 3. 數據抓取函數 (增加容錯機制) ---
@st.cache_data(ttl=3600)
def fetch_all_data(tk):
    stock = yf.Ticker(tk)
    # 確保抓取足夠長度的歷史數據用於回測
    hist = stock.history(period="10y")
    return {
        "info": stock.info,
        "hist": hist,
        "news": stock.news if stock.news else []
    }

try:
    with st.spinner('AI 正在分析數據...'):
        d = fetch_all_data(symbol)
        info, hist = d["info"], d["hist"]
        curr_price = info.get('currentPrice') or (hist['Close'].iloc[-1] if not hist.empty else 0)

    # --- A. 智能健康燈號 & 利多利空 ---
    st.subheader("🤖 AI 診斷報告")
    score = 0
    reasons_pro = []
    reasons_con = []

    # 評分邏輯 1: 本益比
    pe = info.get('trailingPE')
    if pe and pe < 20: 
        score += 1
        reasons_pro.append("估值合理 (P/E < 20)")
    elif pe:
        reasons_con.append(f"估值偏高 (P/E: {pe:.1f})")

    # 評分邏輯 2: 籌碼面 (空單)
    short_pct = info.get('shortPercentOfFloat', 0)
    if short_pct < 0.05:
        score += 1
        reasons_pro.append("籌碼穩定 (空單比例低)")
    else:
        reasons_con.append("空方關注 (空單比例較高)")

    # 評分邏輯 3: 營收成長
    rev_growth = info.get('revenueGrowth')
    if rev_growth and rev_growth > 0.1:
        score += 1
        reasons_pro.append("營收強勁成長")

    # 顯示燈號
    l1, l2 = st.columns([1, 3])
    with l1:
        if score >= 2:
            st.success("🟢 健康燈號：表現優異")
        elif score == 1:
            st.warning("🟡 健康燈號：中性觀察")
        else:
            st.error("🔴 健康燈號：需警惕")
    
    with l2:
        st.write(f"**利多因素：** {', '.join(reasons_pro) if reasons_pro else '無'}")
        st.write(f"**利空因素：** {', '.join(reasons_con) if reasons_con else '無'}")

    # --- B. 定期定額回測 ---
    st.divider()
    st.subheader("📅 定期定額回測分析")
    if not hist.empty:
        # 截取使用者選擇的年數
        backtest_df = hist.last(f"{invest_years}Y").copy()
        # 每月第一筆交易日買入
        monthly_df = backtest_df.resample('MS').first()
        
        total_invested = 0
        total_shares = 0
        for p in monthly_df['Close']:
            total_shares += monthly_invest / p
            total_invested += monthly_invest
        
        current_val = total_shares * curr_price
        roi = ((current_val - total_invested) / total_invested) * 100
        
        b1, b2, b3 = st.columns(3)
        b1.metric("累積投入本金", f"${total_invested:,.0f}")
        b2.metric("期末資產價值", f"${current_val:,.0f}")
        b3.metric("累積報酬率", f"{roi:.2f}%", delta=f"{roi:.2f}%")
        
        st.line_chart(backtest_df['Close'])

    # --- C. 關鍵消息 (修正 'title' Bug) ---
    st.divider()
    m1, m2 = st.columns(2)
    
    with m1:
        st.subheader("📰 關鍵消息")
        if d["news"]:
            for n in d["news"][:5]:
                # 使用 .get() 安全獲取標題，若無則顯示 'No Title'
                # yfinance news 結構可能因版本而異，同時檢查 title 與 headline
                title = n.get('title') or n.get('headline') or "未提供標題"
                link = n.get('link') or "#"
                st.markdown(f"🔗 [{title}]({link})")
        else:
            st.write("暫無相關新聞。")
    
    with m2:
        st.subheader("👥 機構籌碼監測")
        inst_own = info.get('heldPercentInstitutions', 0) * 100
        insider_own = info.get('heldPercentInsiders', 0) * 100
        st.metric("法人持股比例", f"{inst_own:.2f}%")
        st.write(f"內部人持股：{insider_own:.2f}%")
        
        if inst_own > 50:
            st.info("💡 法人高度持股，股價波動通常較具防禦性。")
        else:
            st.write("💡 散戶比例較高，股價波動可能較劇烈。")

except Exception as e:
    st.error(f"系統異常：{str(e)}")
    st.info("建議檢查代號是否正確。台股代號請參考 yfinance 格式，例如 2330.TW。")
