import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Real-Time Portfolio Tracker", layout="centered")

st.title("📈 Real-Time Portfolio Tracker")

st.sidebar.header("Enter Your Portfolio")

default_tickers = "VOO, GOOGL, NU, GRAB, AMD, ASML, QCOM, TSM, XLU, IAU"
tickers_input = st.sidebar.text_input("Tickers (comma-separated):", default_tickers)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

shares_input = st.sidebar.text_area("Shares (match ticker order):", "10, 5, 20, 50, 8, 4, 6, 10, 7, 15")
try:
    shares = [int(s.strip()) for s in shares_input.split(",")]
except ValueError:
    st.error("Please enter valid integers for shares.")
    st.stop()

if len(tickers) != len(shares):
    st.error("The number of tickers and shares must match.")
    st.stop()

st.info("Fetching latest prices...")
data = yf.download(tickers, period="1d", interval="1d", group_by='ticker', auto_adjust=True, threads=True)

portfolio_data = []
for i in range(len(tickers)):
    ticker = tickers[i]
    try:
        price = data[ticker]["Close"].iloc[-1]
    except Exception:
        price = None
    if price is not None:
        value = round(price * shares[i], 2)
        portfolio_data.append([ticker, shares[i], round(price, 2), value])
    else:
        portfolio_data.append([ticker, shares[i], "N/A", "N/A"])

df = pd.DataFrame(portfolio_data, columns=["Ticker", "Shares", "Price", "Value"])
total_value = df["Value"].replace("N/A", 0).astype(float).sum()
df["Allocation %"] = round((df["Value"].replace("N/A", 0).astype(float) / total_value) * 100, 2)

st.subheader("📊 Portfolio Breakdown")
st.dataframe(df)
st.markdown(f"### 💰 Total Portfolio Value: ${total_value:,.2f}")

# Filter valid rows for charts
df_valid = df[df["Value"] != "N/A"].copy()
df_valid["Value"] = df_valid["Value"].astype(float)

# Donut chart
fig_donut = px.pie(
    df_valid,
    names="Ticker",
    values="Value",
    hole=0.4,
    title="Portfolio Allocation by Value",
    color_discrete_sequence=px.colors.qualitative.Set3
)
st.plotly_chart(fig_donut, use_container_width=True)

# Bar chart
fig_bar = px.bar(
    df_valid,
    x="Ticker",
    y="Value",
    text="Value",
    title="Asset Value per Ticker",
    color="Ticker"
)
fig_bar.update_traces(texttemplate='$%{text:.2s}', textposition='outside')
fig_bar.update_layout(yaxis_title="USD", xaxis_title="", showlegend=False)
st.plotly_chart(fig_bar, use_container_width=True)

# Optional line chart per ticker
if st.checkbox("📈 Show 7-Day Price Trends"):
    trend_data = yf.download(tickers, period="7d", interval="1d", group_by="ticker", auto_adjust=True)
    for ticker in tickers:
        try:
            prices = trend_data[ticker]["Close"]
            fig_line = px.line(prices, title=f"{ticker} Price Trend (7D)")
            st.plotly_chart(fig_line, use_container_width=True)
        except Exception:
            st.warning(f"No data for {ticker}")
