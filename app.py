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
monthly_invest = st.sidebar.number_input("每月定期定額金額 ($)", value=1000, step=100)
invest_years = st.sidebar.slider("回測年數", 1, 10, 3)

@st.cache_data(ttl=3600)
def fetch_all_data(tk):
    stock = yf.Ticker(tk)
    # 抓取較長歷史以供回測
    hist = stock.history(period="10y")
    return {
        "info": stock.info,
        "hist": hist,
        "news": stock.news if stock.news else []
    }

try:
    with st.spinner('數據同步中...'):
        d = fetch_all_data(symbol)
        info, hist = d["info"], d["hist"]
        curr_price = info.get('currentPrice') or (hist['Close'].iloc[-1] if not hist.empty else 0)

    # --- A. 智能健康燈號 ---
    st.subheader("🤖 AI 診斷報告")
    score = 0
    reasons_pro, reasons_con = [], []

    # 簡單邏輯：PE 與 營收成長
    pe = info.get('trailingPE')
    if pe and pe < 25: 
        score += 1
        reasons_pro.append(f"估值合理 (P/E: {pe:.1f})")
    elif pe:
        reasons_con.append(f"估值偏高 (P/E: {pe:.1f})")

    rev_growth = info.get('revenueGrowth')
    if rev_growth and rev_growth > 0.1:
        score += 1
        reasons_pro.append("營收雙位數成長")

    c_l1, c_l2 = st.columns([1, 3])
    with c_l1:
        if score >= 2: st.success("🟢 健康燈號：表現優異")
        elif score == 1: st.warning("🟡 健康燈號：中性觀察")
        else: st.error("🔴 健康燈號：需警惕")
    with c_l2:
        st.write(f"**利多：** {', '.join(reasons_pro) if reasons_pro else '無'}")
        st.write(f"**利空：** {', '.join(reasons_con) if reasons_con else '無'}")

    # --- B. 定期定額回測 ---
    st.divider()
    st.subheader("📅 定期定額回測分析")
    if not hist.empty:
        backtest_df = hist.last(f"{invest_years}Y").copy()
        monthly_df = backtest_df.resample('MS').first()
        total_inv = len(monthly_df) * monthly_invest
        total_shares = (monthly_invest / monthly_df['Close']).sum()
        curr_val = total_shares * curr_price
        roi = ((curr_val - total_inv) / total_inv) * 100
        
        b1, b2, b3 = st.columns(3)
        b1.metric("累積投入本金", f"${total_inv:,.0f}")
        b2.metric("期末資產價值", f"${curr_val:,.0f}")
        b3.metric("累積報酬率", f"{roi:.2f}%", delta=f"{roi:.2f}%")
        st.line_chart(backtest_df['Close'])

    # --- C. 關鍵消息 (修正點不開的 Bug) ---
    st.divider()
    m1, m2 = st.columns(2)
    
    with m1:
        st.subheader("📰 關鍵消息")
        if d["news"]:
            for n in d["news"][:5]:
                # 強化標題抓取：依序檢查不同可能的鍵值
                title = n.get('title') or n.get('headline') or "點擊查看新聞內容"
                
                # 強化連結抓取：yfinance 有時會把連結放在不同的地方
                # 依序嘗試：'link', 'url', 'provider_url'
                link = n.get('link') or n.get('url') or n.get('provider_url')
                
                if link:
                    st.markdown(f"✅ **[{title}]({link})**")
                else:
                    st.write(f"⚪ {title} (暫無外部連結)")
        else:
            st.write("暫無新聞。")
    
    with m2:
        st.subheader("👥 法人籌碼")
        inst = info.get('heldPercentInstitutions', 0) * 100
        st.metric("法人持股比例", f"{inst:.2f}%")
        if inst > 50: st.info("💡 法人高度持股，籌碼相對穩定。")
        else: st.write("💡 散戶比例較高。")

except Exception as e:
    st.error(f"系統異常：{str(e)}")
