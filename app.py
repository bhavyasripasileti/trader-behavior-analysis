import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Trader Analytics Dashboard", layout="wide")

st.title("📊 Trader Behavior Intelligence Dashboard")

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("notebooks/final_output.csv")
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

df = load_data()

if df is None:
    st.stop()

# ---------------- CLEAN + FIX COLUMNS ----------------
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Fix missing columns
if 'size_usd' in df.columns:
    df['risk_score'] = df['size_usd']

if 'classification' in df.columns:
    df['sentiment'] = df['classification']

# Create sentiment_score if missing
if 'sentiment_score' not in df.columns and 'sentiment' in df.columns:
    mapping = {
        "Extreme Fear": 0,
        "Fear": 0,
        "Greed": 1,
        "Extreme Greed": 1
    }
    df['sentiment_score'] = df['sentiment'].map(mapping)

# Ensure profit column exists
if 'profit' not in df.columns and 'closed_pnl' in df.columns:
    df['profit'] = df['closed_pnl'] > 0

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filters")

if 'sentiment' in df.columns:
    sentiment_options = ["All"] + list(df['sentiment'].dropna().unique())
    sentiment_filter = st.sidebar.selectbox("Select Sentiment", sentiment_options)

    if sentiment_filter != "All":
        df = df[df['sentiment'] == sentiment_filter]

# ---------------- KPIs ----------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Trades", len(df))

if 'closed_pnl' in df.columns:
    col2.metric("Total PnL", f"{df['closed_pnl'].sum():,.2f}")

if 'profit' in df.columns:
    col3.metric("Win Rate", f"{df['profit'].mean()*100:.2f}%")

# ---------------- CHARTS ----------------
st.subheader("📈 PnL vs Market Sentiment")

if 'sentiment_score' in df.columns and 'closed_pnl' in df.columns:
    fig1 = px.box(
        df,
        x="sentiment_score",
        y="closed_pnl",
        title="PnL vs Market Sentiment"
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.warning("Required columns missing for PnL vs Sentiment chart")

st.subheader("📊 Risk vs Return")

if 'risk_score' in df.columns and 'closed_pnl' in df.columns:
    fig2 = px.scatter(
        df,
        x="risk_score",
        y="closed_pnl",
        title="Risk vs Return"
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Required columns missing for Risk vs Return chart")

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
