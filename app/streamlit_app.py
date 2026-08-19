# FORESIGHT dashboard dependencies: streamlit, pandas, numpy, plotly
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="FORESIGHT | Demand & Inventory Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / "outputs"

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
    .stApp { background: #f6f8fb; }
    [data-testid="stSidebar"] { background: #111827; }
    [data-testid="stSidebar"] * { color: #f9fafb !important; }

    /* Correct readable selectbox text on the dark sidebar */
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        background: #f8fafc !important;
        border-radius: 12px !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #f8fafc !important;
        color: #111827 !important;
        border-color: #e2e8f0 !important;
        border-radius: 12px !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] div,
    section[data-testid="stSidebar"] [data-baseweb="select"] span,
    section[data-testid="stSidebar"] [data-baseweb="select"] input {
        color: #111827 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] svg {
        fill: #334155 !important;
    }
    [data-baseweb="popover"] { background: #ffffff !important; }
    [data-baseweb="popover"] *,
    [data-baseweb="popover"] li { color: #111827 !important; }
    [data-baseweb="popover"] li:hover { background: #e2e8f0 !important; }
    .brand { padding: 4px 0 18px 0; }
    .brand-title { font-size: 2.15rem; font-weight: 800; letter-spacing: .08em; margin: 0; color: #111827; }
    .brand-subtitle { margin: 2px 0 0 0; color: #64748b; font-size: .95rem; }
    .hero { background: linear-gradient(135deg, #111827 0%, #1f2937 55%, #334155 100%); border-radius: 18px; padding: 26px 30px; color: white; margin-bottom: 18px; box-shadow: 0 8px 30px rgba(15,23,42,.12); }
    .hero h1 { margin: 0; font-size: 2rem; letter-spacing: .06em; }
    .hero p { margin: 7px 0 0 0; color: #cbd5e1; }
    .kpi { background: white; border: 1px solid #e5e7eb; border-radius: 15px; padding: 17px 18px; min-height: 112px; box-shadow: 0 4px 18px rgba(15,23,42,.05); }
    .kpi-label { color: #64748b; font-size: .82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; }
    .kpi-value { color: #111827; font-size: 1.65rem; font-weight: 800; margin-top: 7px; }
    .kpi-note { color: #94a3b8; font-size: .76rem; margin-top: 3px; }
    .section-title { font-size: 1.15rem; font-weight: 800; color: #111827; margin: 14px 0 8px 0; }
    .insight { background: white; border-left: 4px solid #2563eb; border-radius: 10px; padding: 13px 16px; margin-bottom: 8px; color: #334155; }
    .action-card { background: white; border-radius: 14px; border: 1px solid #e5e7eb; padding: 15px; }
    .small-muted { color: #64748b; font-size: .82rem; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #e5e7eb; border-radius: 14px; padding: 12px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Data loading
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data():
    repl = pd.read_csv(OUT / "replenishment_recommendations.csv")
    forecast = pd.read_csv(OUT / "forecast_results.csv")
    scores = pd.read_csv(OUT / "model_scores.csv")
    forecast["week"] = pd.to_datetime(forecast["week"], errors="coerce")
    for c in ["stock_on_hand", "ROP", "EOQ", "forecast_8w_demand", "reorder_qty", "sales_at_risk_rupees", "locked_capital_rupees", "priority_score"]:
        if c in repl.columns:
            repl[c] = pd.to_numeric(repl[c], errors="coerce").fillna(0)
    return repl, forecast, scores

try:
    repl, forecast, scores = load_data()
except FileNotFoundError:
    st.error("FORESIGHT outputs are missing. Add the generated CSV files to the project's outputs/ folder, then restart Streamlit.")
    st.stop()
except Exception as exc:
    st.error(f"FORESIGHT could not load its data: {exc}")
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("## FORESIGHT")
st.sidebar.caption("AI-Powered Demand & Inventory Intelligence")
st.sidebar.divider()
st.sidebar.markdown("### Planning Controls")

categories = ["All Categories"] + sorted(repl["category"].dropna().astype(str).unique().tolist())
actions = ["All Actions"] + sorted(repl["recommended_action"].dropna().astype(str).unique().tolist())

selected_category = st.sidebar.selectbox("Category", categories)
selected_action = st.sidebar.selectbox("Action", actions)

min_stock, max_stock = float(repl["stock_on_hand"].min()), float(repl["stock_on_hand"].max())
stock_filter = st.sidebar.checkbox("Focus on low-stock / high-risk SKUs", value=False)
top_n = st.sidebar.slider("Rows in action table", 10, 100, 25, 5)

view = repl.copy()
if selected_category != "All Categories":
    view = view[view["category"] == selected_category]
if selected_action != "All Actions":
    view = view[view["recommended_action"] == selected_action]
if stock_filter:
    view = view[view["stockout_risk"] | view["overstock_risk"]]

selected_sku = st.sidebar.selectbox(
    "SKU drill-down",
    ["All SKUs"] + sorted(view["sku_id"].astype(str).unique().tolist()),
)
if selected_sku != "All SKUs":
    view = view[view["sku_id"] == selected_sku]

st.sidebar.divider()
st.sidebar.caption("Recommendations are for human review. FORESIGHT does not place purchase orders automatically.")

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="hero">
  <h1>FORESIGHT</h1>
  <p>AI-Powered Demand & Inventory Intelligence Platform · Executive Operations View</p>
</div>
""", unsafe_allow_html=True)

latest_week = forecast["week"].max().strftime("%d %b %Y") if forecast["week"].notna().any() else "—"

# -----------------------------
# KPI calculations
# -----------------------------
reorder_count = int((view["recommended_action"] == "REORDER NOW").sum())
markdown_count = int((view["recommended_action"] == "MARKDOWN / CLEAR").sum())
watch_count = int((view["recommended_action"] == "WATCH / VOLATILE").sum())
sales_risk = float(view["sales_at_risk_rupees"].sum())
locked_capital = float(view["locked_capital_rupees"].sum())
units_to_reorder = float(view["reorder_qty"].sum())

kpis = [
    ("SKUs in View", f"{len(view):,}", "Filtered planning universe"),
    ("Reorder Now", f"{reorder_count:,}", "Immediate replenishment candidates"),
    ("Sales at Risk", f"₹{sales_risk/1e6:.2f}M", "Estimated stockout exposure"),
    ("Locked Capital", f"₹{locked_capital/1e6:.2f}M", "Estimated overstock capital"),
    ("Markdown / Clear", f"{markdown_count:,}", "Overstock candidates"),
    ("Units to Reorder", f"{units_to_reorder:,.0f}", "Recommended order quantity"),
]
cols = st.columns(6)
for col, (label, value, note) in zip(cols, kpis):
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)

st.caption(f"Data-driven planning view · Forecast data through {latest_week}")

# -----------------------------
# Main tabs
# -----------------------------
tab_overview, tab_forecast, tab_actions, tab_model = st.tabs([
    "Executive Overview", "Demand Forecast", "Inventory Action Center", "Model Performance"
])

# -----------------------------
# Overview
# -----------------------------
with tab_overview:
    left, right = st.columns([1.45, 1])

    with left:
        st.markdown('<div class="section-title">Weekly Demand & Forecast</div>', unsafe_allow_html=True)
        if selected_sku != "All SKUs":
            f = forecast[forecast["sku_id"] == selected_sku].sort_values("week")
        else:
            f = forecast.groupby("week", as_index=False).agg(demand=("demand", "sum"), forecast=("forecast", "sum"))
        if not f.empty:
            long_f = f.melt("week", value_vars=["demand", "forecast"], var_name="series", value_name="units")
            long_f["series"] = long_f["series"].map({"demand": "Actual Demand", "forecast": "Forecast"})
            fig = px.line(long_f, x="week", y="units", color="series", markers=True,
                          labels={"week": "Week", "units": "Units", "series": ""})
            fig.update_layout(height=380, margin=dict(l=10,r=10,t=15,b=10), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown('<div class="section-title">Decision Mix</div>', unsafe_allow_html=True)
        mix = view["recommended_action"].value_counts().reset_index()
        mix.columns = ["action", "count"]
        if not mix.empty:
            fig = px.pie(mix, values="count", names="action", hole=.58)
            fig.update_layout(height=380, margin=dict(l=5,r=5,t=15,b=5), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">Risk by Category</div>', unsafe_allow_html=True)
        cat = view.groupby("category", as_index=False).agg(
            sales_at_risk=("sales_at_risk_rupees", "sum"),
            locked_capital=("locked_capital_rupees", "sum")
        ).sort_values("sales_at_risk", ascending=False).head(12)
        cat_long = cat.melt("category", var_name="risk_type", value_name="rupees")
        cat_long["risk_type"] = cat_long["risk_type"].map({"sales_at_risk": "Sales at Risk", "locked_capital": "Locked Capital"})
        fig = px.bar(cat_long, x="rupees", y="category", color="risk_type", orientation="h", barmode="group")
        fig.update_layout(height=420, margin=dict(l=10,r=10,t=10,b=10), xaxis_title="₹", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">Top Priority SKUs</div>', unsafe_allow_html=True)
        top = view.sort_values("priority_score", ascending=False).head(10).copy()
        top["display"] = top["sku_id"] + " · " + top["recommended_action"]
        fig = px.bar(top.sort_values("priority_score"), x="priority_score", y="display", orientation="h")
        fig.update_layout(height=420, margin=dict(l=10,r=10,t=10,b=10), xaxis_title="Priority impact (₹)", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Forecast tab
# -----------------------------
with tab_forecast:
    st.markdown('<div class="section-title">Demand Forecast Explorer</div>', unsafe_allow_html=True)
    if selected_sku == "All SKUs":
        st.info("Select a SKU in the sidebar to inspect its individual forecast. The overview shows the aggregate demand curve.")
        summary = forecast.groupby("week", as_index=False).agg(actual=("demand", "sum"), forecast=("forecast", "sum"))
        fig = px.line(summary, x="week", y=["actual", "forecast"], markers=True)
        fig.update_layout(height=450, margin=dict(l=10,r=10,t=20,b=10), legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
    else:
        f = forecast[forecast["sku_id"] == selected_sku].sort_values("week").copy()
        if f.empty:
            st.warning("No forecast records found for this SKU.")
        else:
            a, b, c = st.columns(3)
            a.metric("Average Actual / Week", f"{f['demand'].mean():,.1f}")
            b.metric("Average Forecast / Week", f"{f['forecast'].mean():,.1f}")
            error = (f["forecast"] - f["demand"]).abs().sum() / max(f["demand"].abs().sum(), 1)
            c.metric("WAPE on displayed history", f"{error:.1%}")
            fig = px.line(f, x="week", y=["demand", "forecast"], markers=True,
                          labels={"value": "Units", "variable": "Series"})
            fig.update_layout(height=470, margin=dict(l=10,r=10,t=20,b=10), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(f, use_container_width=True, hide_index=True)

# -----------------------------
# Action Center
# -----------------------------
with tab_actions:
    st.markdown('<div class="section-title">What should the operations team do?</div>', unsafe_allow_html=True)
    st.markdown('<div class="insight"><b>REORDER NOW</b> = stockout risk requiring replenishment. <b>MARKDOWN / CLEAR</b> = overstock exposure. <b>WATCH / VOLATILE</b> = conflicting signals requiring review.</div>', unsafe_allow_html=True)

    action_cols = [
        "sku_id", "sku_name", "category", "stock_on_hand", "ROP", "EOQ", "forecast_8w_demand",
        "recommended_action", "reorder_qty", "sales_at_risk_rupees", "locked_capital_rupees"
    ]
    action_table = view[action_cols].copy().sort_values(
        ["sales_at_risk_rupees", "locked_capital_rupees"], ascending=False
    ).head(top_n)
    st.dataframe(
        action_table.style.format({
            "stock_on_hand": "{:,.0f}", "ROP": "{:,.1f}", "EOQ": "{:,.1f}",
            "forecast_8w_demand": "{:,.1f}", "reorder_qty": "{:,.0f}",
            "sales_at_risk_rupees": "₹{:,.0f}", "locked_capital_rupees": "₹{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True,
    )

    download = view.sort_values("priority_score", ascending=False).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download Prioritised Replenishment Report",
        data=download,
        file_name="foresight_replenishment_report.csv",
        mime="text/csv",
        use_container_width=False,
    )

# -----------------------------
# Model tab
# -----------------------------
with tab_model:
    st.markdown('<div class="section-title">Forecasting Model Performance</div>', unsafe_allow_html=True)
    st.caption("WAPE is the primary accuracy metric; lower is better. Bias is a secondary diagnostic.")

    score = scores.copy()
    if "WAPE" in score.columns:
        score["WAPE"] = pd.to_numeric(score["WAPE"], errors="coerce")
    if "Bias" in score.columns:
        score["Bias"] = pd.to_numeric(score["Bias"], errors="coerce")

    best = score.sort_values("WAPE").iloc[0] if not score.empty else None
    if best is not None:
        m1, m2, m3 = st.columns(3)
        m1.metric("Best WAPE", f"{best['WAPE']:.1%}")
        m2.metric("Best Model", str(best["Model"]))
        m3.metric("Bias", f"{best['Bias']:+.3f}")

    if not score.empty:
        chart = px.bar(score.sort_values("WAPE"), x="Model", y="WAPE", text_auto=".1%", title="WAPE comparison — lower is better")
        chart.update_layout(height=380, margin=dict(l=10,r=10,t=45,b=10), yaxis_tickformat=".0%")
        st.plotly_chart(chart, use_container_width=True)
        st.dataframe(score, use_container_width=True, hide_index=True)

    st.markdown('<div class="insight"><b>Governance:</b> Model performance should be judged against a seasonal-naive baseline using time-aware backtesting. Do not claim a complex model is better unless the recorded backtest supports it.</div>', unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.divider()
st.caption("FORESIGHT · Demand Forecasting · Stockout Early Warning · Overstock Intelligence · Replenishment Decision Support")
