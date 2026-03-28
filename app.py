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


# ---------------- SAFE VISUALIZATION ----------------

# Convert safely
df['closed_pnl'] = pd.to_numeric(df['closed_pnl'], errors='coerce')
df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce')
df['sentiment_score'] = pd.to_numeric(df['sentiment_score'], errors='coerce')

# Drop only NULLs (NOT zeros)
df_viz = df.dropna(subset=['closed_pnl', 'risk_score', 'sentiment_score']).copy()

# 🔥 LIMIT DATA (important for Streamlit)
df_viz = df_viz.sample(min(3000, len(df_viz)))

# 🔥 SIMPLE SCALING (NOT complex transform)
df_viz['closed_pnl_scaled'] = df_viz['closed_pnl'] / 1000
df_viz['risk_score_scaled'] = df_viz['risk_score'] / 1000

# ---------------- AGGREGATED ANALYSIS (FINAL FIX) ----------------

# Clean numeric
df['closed_pnl'] = pd.to_numeric(df['closed_pnl'], errors='coerce')
df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce')

# Drop NaN
df_clean = df.dropna(subset=['closed_pnl', 'risk_score', 'sentiment_score'])

# 🔥 AGGREGATE DATA (KEY STEP)
agg_df = df_clean.groupby('sentiment_score').agg({
    'closed_pnl': 'mean',
    'risk_score': 'mean'
}).reset_index()

# ---------------- CHART 1 ----------------
st.subheader("📈 Avg PnL vs Market Sentiment")

fig1 = px.bar(
    agg_df,
    x='sentiment_score',
    y='closed_pnl',
    title="Average PnL by Sentiment",
    text_auto=True
)
st.plotly_chart(fig1, use_container_width=True)

# ---------------- CHART 2 ----------------
st.subheader("📊 Avg Risk vs Return")

fig2 = px.scatter(
    agg_df,
    x='risk_score',
    y='closed_pnl',
    size='closed_pnl',
    color='sentiment_score',
    title="Risk vs Return (Aggregated)",
    text='sentiment_score'
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
