import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Advanced Portfolio Tracker", layout="wide")

st.title("📈 Advanced Real-Time Portfolio Tracker")

# Sidebar inputs
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

# Fetch latest prices and historical data
st.info("Fetching data...")

try:
    data_latest = yf.download(tickers, period="1d", interval="1d", group_by='ticker', auto_adjust=True, threads=True)
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    data_hist = yf.download(tickers, start=start_date.strftime('%Y-%m-%d'), group_by='ticker', auto_adjust=True)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# Prepare portfolio DataFrame
portfolio_data = []
for i, ticker in enumerate(tickers):
    try:
        price = data_latest[ticker]["Close"].iloc[-1]
        # Get previous close for gain/loss
        prev_close = data_hist[ticker]["Close"].iloc[0] if ticker in data_hist else None
        value = price * shares[i]
        cost_basis = prev_close * shares[i] if prev_close else None
        gain_loss_abs = value - cost_basis if cost_basis else None
        gain_loss_pct = (gain_loss_abs / cost_basis * 100) if cost_basis else None
        portfolio_data.append([ticker, shares[i], price, value, gain_loss_abs, gain_loss_pct])
    except Exception:
        portfolio_data.append([ticker, shares[i], None, None, None, None])

df = pd.DataFrame(portfolio_data, columns=["Ticker", "Shares", "Price", "Value", "Gain/Loss ($)", "Gain/Loss (%)"])

# Format currency and percentages
df["Price_fmt"] = df["Price"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
df["Value_fmt"] = df["Value"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
df["Gain/Loss ($)_fmt"] = df["Gain/Loss ($)"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
df["Gain/Loss (%)_fmt"] = df["Gain/Loss (%)"].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")

total_value = df["Value"].dropna().sum()

# Allocation %
df["Allocation %"] = df["Value"].fillna(0) / total_value * 100

# Function for coloring gain/loss
def gain_loss_color(val):
    if pd.isnull(val):
        return ""
    if val > 0:
        return "color: green; font-weight: bold"
    elif val < 0:
        return "color: red; font-weight: bold"
    else:
        return ""

# Get logo URLs using Clearbit (free logo API)
def get_logo_url(ticker):
    # This is a trick: Clearbit logos for domains, map tickers to company domain manually for demo
    mapping = {
        "GOOGL": "google.com",
        "AMD": "amd.com",
        "ASML": "asml.com",
        "QCOM": "qualcomm.com",
        "TSM": "tsmc.com",
        "VOO": "vanguard.com",
        "NU": "nu.com",
        "GRAB": "grab.com",
        "XLU": "xlucorp.com",
        "IAU": "ishares.com"
    }
    domain = mapping.get(ticker, None)
    if domain:
        return f"https://logo.clearbit.com/{domain}"
    else:
        return ""

df["Logo"] = df["Ticker"].apply(get_logo_url)

# Show portfolio with logos and color-coded gain/loss
st.subheader("📊 Portfolio Breakdown with Gain/Loss and Logos")

def render_logo(t):
    url = get_logo_url(t)
    if url:
        return f'<img src="{url}" width="30" height="30">'
    return ""

df_display = df[["Ticker", "Shares", "Price_fmt", "Value_fmt", "Gain/Loss ($)_fmt", "Gain/Loss (%)_fmt", "Allocation %"]].copy()
df_display.columns = ["Ticker", "Shares", "Price", "Value", "Gain/Loss ($)", "Gain/Loss (%)", "Allocation %"]

# Render logos next to ticker
df_display["Ticker"] = df_display["Ticker"].apply(lambda t: f'{render_logo(t)} {t}')
st.write("Logos courtesy of Clearbit Logo API")

# Use st.markdown to enable rendering html images in dataframe
st.markdown(
    df_display.to_html(escape=False, index=False),
    unsafe_allow_html=True,
)

# Highlight gain/loss columns
def highlight_gain_loss(s):
    return ['color: green; font-weight:bold' if (v := float(str(x).replace("$", "").replace(",", "").replace("%", ""))) > 0
            else 'color: red; font-weight:bold' if v < 0 else '' for x in s]

# Line chart: portfolio total value over last 30 days
portfolio_value = pd.DataFrame()
for i, ticker in enumerate(tickers):
    if ticker in data_hist:
        portfolio_value[ticker] = data_hist[ticker]['Close'] * shares[i]
portfolio_value['Total'] = portfolio_value.sum(axis=1)

st.subheader("📅 Portfolio Value Over Last 30 Days")
fig_line = px.line(portfolio_value, y='Total', title='Portfolio Value Over Time',
                   labels={'index': 'Date', 'Total': 'Portfolio Value ($)'},
                   template='plotly_dark')
st.plotly_chart(fig_line, use_container_width=True)

# Bar chart: current value by stock with logos as annotations
df_bar = df.dropna(subset=["Value"])
fig_bar = px.bar(df_bar, x="Ticker", y="Value", text=df_bar["Value"].apply(lambda x: f"${x:,.2f}"),
                 title="💵 Current Value by Stock",
                 labels={"Value": "Value ($)", "Ticker": "Stock"},
                 template='plotly_dark')

fig_bar.update_traces(textposition="outside")

# Add logos as annotations above bars
for i, row in df_bar.iterrows():
    logo_url = row["Logo"]
    if logo_url:
        fig_bar.add_layout_image(
            dict(
                source=logo_url,
                x=row["Ticker"],
                y=row["Value"] + total_value*0.02,
                xref="x",
                yref="y",
                sizex=0.3,
                sizey=total_value*0.05,
                xanchor="center",
                yanchor="bottom",
                layer="above"
            )
        )

st.plotly_chart(fig_bar, use_container_width=True)

# Individual stock price trends
st.subheader("📈 Individual Stock Price Trends (Last 30 Days)")
for ticker in tickers:
    if ticker in data_hist:
        st.markdown(f"**{ticker}**")
        fig = px.line(data_hist[ticker], y='Close', title=f'{ticker} Price Last 30 Days',
                      labels={'Date': 'Date', 'Close': 'Price ($)'},
                      template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
