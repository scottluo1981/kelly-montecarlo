# -*- coding: utf-8 -*-
"""
股票期望值 × 凱利公式 × 蒙地卡羅模擬
Streamlit 互動版
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="凱利公式 × 蒙地卡羅估值",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== Sidebar 輸入 ==========
st.sidebar.title("📊 參數設定")

st.sidebar.header("一、基本參數")
cost_price = st.sidebar.number_input("現價 / 成本價", value=468.0, min_value=1.0, step=1.0, format="%.2f")
forecast_eps = st.sidebar.number_input("預估 EPS", value=7.0, min_value=0.01, step=0.1, format="%.2f")
shares = st.sidebar.number_input("持股數量（僅蒙地卡羅用）", value=2000, min_value=1, step=100)

st.sidebar.header("二、估值重估設定")
use_rerate = st.sidebar.selectbox("使用重估本益比？", ["是", "否"], index=0)

if use_rerate == "是":
    pe_opt = st.sidebar.number_input("樂觀重估本益比", value=50.0, min_value=1.0, step=1.0)
    pe_neu = st.sidebar.number_input("中性重估本益比", value=35.0, min_value=1.0, step=1.0)
    pe_pes = st.sidebar.number_input("悲觀重估本益比", value=20.0, min_value=1.0, step=1.0)
else:
    avg_pe = st.sidebar.number_input("歷史平均本益比", value=25.0, min_value=1.0, step=1.0)
    pe_std = st.sidebar.number_input("本益比標準差", value=8.0, min_value=0.1, step=0.5)
    pe_opt = avg_pe + pe_std
    pe_neu = avg_pe
    pe_pes = max(1.0, avg_pe - pe_std)

st.sidebar.header("三、情境機率")
p_opt = st.sidebar.slider("樂觀機率", 0.0, 1.0, 0.30, 0.05)
p_neu = st.sidebar.slider("中性機率", 0.0, 1.0, 0.50, 0.05)
p_pes = st.sidebar.slider("悲觀機率", 0.0, 1.0, 0.20, 0.05)
prob_sum = p_opt + p_neu + p_pes
if abs(prob_sum - 1.0) > 0.01:
    st.sidebar.warning(f"機率合計 = {prob_sum:.0%}，建議調整為 100%")

st.sidebar.header("四、蒙地卡羅設定")
n_sim = st.sidebar.number_input("模擬次數", value=2000, min_value=100, max_value=20000, step=500)
eps_vol = st.sidebar.slider("EPS 隨機波動 (±)", 0.0, 0.30, 0.05, 0.01)
growth_for_mc = st.sidebar.number_input("蒙地卡羅用成長率（若用去年EPS）", value=0.75, min_value=-0.5, max_value=3.0, step=0.05, format="%.2f")
use_forecast_eps = st.sidebar.checkbox("蒙地卡羅直接使用上方「預估 EPS」", value=True)

# ========== 計算目標價 ==========
target_opt = forecast_eps * pe_opt
target_neu = forecast_eps * pe_neu
target_pes = forecast_eps * pe_pes

ret_opt = (target_opt - cost_price) / cost_price
ret_neu = (target_neu - cost_price) / cost_price
ret_pes = (target_pes - cost_price) / cost_price

payoff_opt = target_opt - cost_price
payoff_neu = target_neu - cost_price
payoff_pes = target_pes - cost_price

# 期望值
ev_amt = p_opt * payoff_opt + p_neu * payoff_neu + p_pes * payoff_pes
ev_rate = ev_amt / cost_price

# 勝率與 Avg Win / Loss
targets = np.array([target_opt, target_neu, target_pes])
probs = np.array([p_opt, p_neu, p_pes])
payoffs = targets - cost_price

win_mask = payoffs > 0
win_rate = probs[win_mask].sum() if win_mask.any() else 0.0
avg_win = payoffs[win_mask].mean() if win_mask.any() else 0.0
avg_loss = abs(payoffs[~win_mask].mean()) if (~win_mask).any() else 0.0
b_ratio = avg_win / avg_loss if avg_loss > 0 else np.nan

if np.isnan(b_ratio) or b_ratio == 0 or win_rate == 0:
    full_kelly = 0.0
else:
    full_kelly = win_rate - (1 - win_rate) / b_ratio
half_kelly = full_kelly * 0.5

# ========== 主畫面 ==========
st.title("📈 股票期望值 × 凱利公式 × 蒙地卡羅")
st.caption("直覺化互動版｜支援估值重估")

# 結果卡片
c1, c2, c3, c4 = st.columns(4)
c1.metric("期望報酬率", f"{ev_rate:.1%}", delta=None)
c2.metric("勝率", f"{win_rate:.0%}")
c3.metric("半凱利建議部位", f"{half_kelly:.1%}", help="實戰推薦使用半凱利或更低")
c4.metric("全凱利建議部位", f"{full_kelly:.1%}")

if ev_rate > 0:
    st.success(f"✅ 正期望值交易｜建議部位約 {half_kelly:.0%}（半凱利）")
else:
    st.error("❌ 目前假設下為負期望值，建議重新檢視 EPS 或本益比假設")

# 情境表
st.subheader("二、情景分析")
df_scenario = pd.DataFrame({
    "情景": ["樂觀", "中性", "悲觀"],
    "機率": [p_opt, p_neu, p_pes],
    "使用本益比": [pe_opt, pe_neu, pe_pes],
    "目標價": [target_opt, target_neu, target_pes],
    "報酬率": [ret_opt, ret_neu, ret_pes],
    "每股盈虧": [payoff_opt, payoff_neu, payoff_pes],
})
df_scenario["機率"] = df_scenario["機率"].apply(lambda x: f"{x:.0%}")
df_scenario["報酬率"] = df_scenario["報酬率"].apply(lambda x: f"{x:.1%}")
df_scenario["目標價"] = df_scenario["目標價"].apply(lambda x: f"{x:,.1f}")
df_scenario["每股盈虧"] = df_scenario["每股盈虧"].apply(lambda x: f"{x:,.1f}")
df_scenario["使用本益比"] = df_scenario["使用本益比"].apply(lambda x: f"{x:.1f}")
st.dataframe(df_scenario, use_container_width=True, hide_index=True)

# 詳細凱利數字
with st.expander("查看詳細凱利計算數字"):
    st.write(f"平均獲利金額 (Avg Win)：{avg_win:,.2f}")
    st.write(f"平均虧損金額 (Avg Loss)：{avg_loss:,.2f}")
    st.write(f"風險報酬比 (b)：{b_ratio:.2f}" if not np.isnan(b_ratio) else "風險報酬比 (b)：N/A")
    st.write(f"期望報酬金額 (每股)：{ev_amt:,.2f}")

# ========== 蒙地卡羅 ==========
st.subheader("三、蒙地卡羅模擬")

if use_forecast_eps:
    base_eps = forecast_eps
    # 若直接用預估EPS，成長率設為0，只保留波動
    growth = 0.0
else:
    base_eps = forecast_eps / (1 + growth_for_mc)  # 反推去年EPS
    growth = growth_for_mc

np.random.seed(42)
eps_sim = base_eps * (1 + growth + np.random.uniform(-eps_vol, eps_vol, n_sim))
pe_sim = np.random.uniform(pe_pes, pe_opt, n_sim)  # 連續均勻，比整數更平滑
fair_sim = eps_sim * pe_sim
pnl_sim = (fair_sim - cost_price) * shares

mc_win_rate = (pnl_sim > 0).mean()
mc_ev = pnl_sim.mean()
mc_avg_fair = fair_sim.mean()
mc_p5 = np.percentile(pnl_sim, 5)
mc_p95 = np.percentile(pnl_sim, 95)

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("蒙地卡羅勝率", f"{mc_win_rate:.1%}")
col_b.metric("平均公平價", f"{mc_avg_fair:,.1f}")
col_c.metric("總期望盈虧", f"{mc_ev:,.0f}")
col_d.metric("5% ~ 95% 分位", f"{mc_p5:,.0f} ~ {mc_p95:,.0f}")

# 直方圖
fig = px.histogram(
    x=pnl_sim,
    nbins=40,
    title="盈虧分布直方圖（蒙地卡羅）",
    labels={"x": "盈虧金額", "y": "次數"},
    color_discrete_sequence=["#2E75B6"]
)
fig.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="損益兩平")
fig.add_vline(x=mc_ev, line_dash="dot", line_color="green", annotation_text=f"期望值 {mc_ev:,.0f}")
fig.update_layout(height=420)
st.plotly_chart(fig, use_container_width=True)

# 公平價分布
fig2 = px.histogram(
    x=fair_sim,
    nbins=40,
    title="模擬公平價分布",
    labels={"x": "公平價", "y": "次數"},
    color_discrete_sequence=["#C65911"]
)
fig2.add_vline(x=cost_price, line_dash="dash", line_color="red", annotation_text=f"成本價 {cost_price}")
fig2.update_layout(height=380)
st.plotly_chart(fig2, use_container_width=True)

# 說明
st.markdown("---")
st.markdown("""
**使用說明**
1. 左側調整參數後，所有結果即時更新。
2. 「使用重估本益比 = 是」時，樂觀/中性/悲觀本益比由你手動決定（適合估值重估情境）。
3. 半凱利為實戰推薦部位，可再依風險承受度降為 1/3 或 1/4。
4. 蒙地卡羅會在你設定的本益比區間內隨機抽樣，並加入 EPS 波動，更接近真實不確定性。
""")
