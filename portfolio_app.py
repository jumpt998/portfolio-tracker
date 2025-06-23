import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Real-Time Portfolio Tracker", layout="centered")

st.title("📈 Real-Time Portfolio Tracker")

st.sidebar.header("Enter Your Portfolio")

# Inputs
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

# Fetch price data
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

# Display portfolio table
st.subheader("📊 Portfolio Breakdown")
st.dataframe(df.style.format({"Price": "${:,.2f}", "Value": "${:,.2f}", "Allocation %": "{:.2f}%"}))

st.markdown(f"### 💰 Total Portfolio Value: ${total_value:,.2f}")

# Pie chart
if total_value > 0:
    fig, ax = plt.subplots()
    ax.pie(df["Value"].replace("N/A", 0).astype(float), labels=df["Ticker"], autopct='%1.1f%%', startangle=90)
    ax.axis("equal")
    st.pyplot(fig)

# Show logos + ticker + shares below chart
st.subheader("🏷️ Tickers and Logos")
cols = st.columns(len(tickers))
for idx, ticker in enumerate(tickers):
    t = yf.Ticker(ticker)
    logo_url = t.info.get("logo_url")
    with cols[idx]:
        if logo_url:
            st.image(logo_url, width=50)
        st.markdown(f"**{ticker}**")
        st.markdown(f"Shares: {shares[idx]}")
