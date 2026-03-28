import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Trader Analytics Dashboard", layout="wide")

st.title("📊 Trader Behavior Intelligence Dashboard")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("notebooks/final_output.csv")
        return df
    except Exception as e:
        return None, str(e)

data = load_data()

if isinstance(data, tuple):
    st.error(f"Error loading data: {data[1]}")
    st.stop()

df = data

# ---------------- CLEAN COLUMN NAMES FIRST ----------------
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# ---------------- FIX COLUMNS ----------------
if 'size_usd' in df.columns:
    df['risk_score'] = df['size_usd']

if 'classification' in df.columns:
    df['sentiment'] = df['classification']

if 'sentiment_score' not in df.columns and 'sentiment' in df.columns:
    mapping = {
        "Extreme Fear": 0,
        "Fear": 0,
        "Greed": 1,
        "Extreme Greed": 1
    }
    df['sentiment_score'] = df['sentiment'].map(mapping)

if 'profit' not in df.columns and 'closed_pnl' in df.columns:
    df['profit'] = df['closed_pnl'] > 0

# ---------------- REDUCE DATA SIZE (VERY IMPORTANT) ----------------
df = df.sample(min(5000, len(df)))  # prevent freezing

# ---------------- FIX NUMERIC DATA ----------------
if 'closed_pnl' in df.columns:
    df['closed_pnl'] = pd.to_numeric(df['closed_pnl'], errors='coerce')

if 'risk_score' in df.columns:
    df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce')

df = df.dropna(subset=['closed_pnl', 'risk_score'])

# Scale for visualization
df['risk_score'] = df['risk_score'] / 1000

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filters")

if 'sentiment' in df.columns:
    options = ["All"] + list(df['sentiment'].dropna().unique())
    selected = st.sidebar.selectbox("Select Sentiment", options)

    if selected != "All":
        df = df[df['sentiment'] == selected]

# ---------------- KPIs ----------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Trades", len(df))

if 'closed_pnl' in df.columns:
    col2.metric("Total PnL", f"{df['closed_pnl'].sum():,.2f}")

if 'profit' in df.columns:
    col3.metric("Win Rate", f"{df['profit'].mean()*100:.2f}%")


# ---------------- BETTER VISUALIZATION ----------------

# Remove zero pnl (important)
df_viz = df[df['closed_pnl'] != 0].copy()

# If still empty, fallback
if len(df_viz) < 50:
    df_viz = df.copy()

# Log transform (THIS IS THE KEY FIX)
df_viz['closed_pnl_log'] = df_viz['closed_pnl'].apply(
    lambda x: 0 if x == 0 else (abs(x))**0.5 * (1 if x > 0 else -1)
)

df_viz['risk_score_log'] = df_viz['risk_score']**0.5

# ---------------- CHARTS ----------------
st.subheader("📈 PnL vs Market Sentiment")

fig1 = px.box(
    df_viz,
    x="sentiment_score",
    y="closed_pnl_log",
    title="PnL Distribution (Transformed)"
)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("📊 Risk vs Return")

fig2 = px.scatter(
    df_viz,
    x="risk_score_log",
    y="closed_pnl_log",
    opacity=0.6,
    title="Risk vs Return (Transformed)"
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------- LEADERBOARD ----------------
if 'account' in df.columns and 'closed_pnl' in df.columns:
    st.subheader("🏆 Top Traders")

    leaderboard = (
        df.groupby("account")["closed_pnl"]
        .sum()
        .reset_index()
        .sort_values(by="closed_pnl", ascending=False)
        .head(10)
    )

    st.dataframe(leaderboard, use_container_width=True)

st.success("✅ Dashboard Loaded Successfully")
