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

# Sidebar
st.sidebar.header("Filters")

sentiment_filter = st.sidebar.selectbox(
    "Select Sentiment",
    ["All", "Fear", "Greed"]
)

# Filter logic
if sentiment_filter != "All":
    df = df[df['sentiment'].str.contains(sentiment_filter)]

# KPIs
col1, col2, col3 = st.columns(3)

col1.metric("Total Trades", len(df))
col2.metric("Total PnL", f"{df['closed_pnl'].sum():,.2f}")
col3.metric("Win Rate", f"{df['profit'].mean()*100:.2f}%")

# Chart 1: PnL vs Sentiment
fig1 = px.box(
    df,
    x="sentiment_score",
    y="closed_pnl",
    title="PnL vs Market Sentiment"
)
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Risk vs Return
fig2 = px.scatter(
    df,
    x="risk_score",
    y="closed_pnl",
    title="Risk vs Return"
)
st.plotly_chart(fig2, use_container_width=True)

# Trader leaderboard
st.subheader("🏆 Top Traders")

leaderboard = df.groupby("account")["closed_pnl"].sum().reset_index()
leaderboard = leaderboard.sort_values(by="closed_pnl", ascending=False).head(10)

st.dataframe(leaderboard)

st.success("Dashboard Loaded Successfully ")
