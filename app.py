import os
import sys
import time
import re
import urllib.request
import requests

# ==========================================================
# 1. INSTALL DEPENDENCIES & SETUP TUNNEL BINARY
# ==========================================================
os.system("pip install -q streamlit plotly yfinance requests streamlit-autorefresh")

if not os.path.exists("cloudflared"):
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    urllib.request.urlretrieve(url, "cloudflared")
    os.chmod("cloudflared", 0o755)

# ==========================================================
# 2. WRITE DYNAMIC DASHBOARD & LOGIN APPLICATION (app.py)
# ==========================================================
app_code = """
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import time
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Stock Invest AI Dashboard & Live Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN STYLING ---
st.markdown('''
<style>
    .stApp {
        background: linear-gradient(180deg, #0b0f19 0%, #111827 100%);
        color: #f3f4f6;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .nav-bar {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 50%, #2563eb 100%);
        padding: 18px 25px;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(79, 70, 229, 0.35);
        margin-bottom: 25px;
    }
    .nav-title {
        color: #ffffff !important;
        font-size: 1.6rem;
        font-weight: 800;
        margin: 0;
    }
    .nav-subtitle {
        color: #e0e7ff !important;
        font-size: 0.9rem;
        margin: 0;
    }
    .modern-card {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 20px 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .modern-card:hover {
        transform: translateY(-3px);
        border-color: #6366f1;
    }
    .card-icon { font-size: 1.4rem; margin-bottom: 6px; }
    .card-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .card-value { font-size: 1.5rem; font-weight: 800; color: #f8fafc; }
    .metric-positive { color: #10b981 !important; }
    .metric-negative { color: #ef4444 !important; }
    .up-tick { color: #10b981 !important; }
    .down-tick { color: #ef4444 !important; }

    .menu-card-container {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 25px 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
        margin-bottom: 20px;
    }

    .team-card {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 22px 15px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .team-card:hover {
        transform: translateY(-4px);
        border-color: #6366f1;
    }
    .team-avatar {
        width: 75px;
        height: 75px;
        border-radius: 50%;
        border: 3px solid #6366f1;
        margin-bottom: 12px;
        background-color: #0f172a;
    }
    .team-name { font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-bottom: 4px; }
    .team-role { font-size: 0.85rem; font-weight: 600; color: #818cf8; margin-bottom: 10px; }
    .team-badge {
        display: inline-block;
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
</style>
''', unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "active_section" not in st.session_state:
    st.session_state.active_section = "Home Hub"

if not st.session_state.authenticated:
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1 style='color: #ffffff;'>⚡ Secure Terminal Login</h1><p style='color: #94a3b8;'>Enter your credentials to access the Stock AI Dashboard</p></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("🔐 Login to Terminal", use_container_width=True)

            if submit_login:
                if username == "admin" and password == "admin123":
                    st.session_state.authenticated = True
                    st.success("Login successful! Loading dashboard...")
                    st.rerun()
                elif username == "om" and password == "team123":
                    st.session_state.authenticated = True
                    st.success(f"Welcome Om! Loading dashboard...")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password. (Hint: admin / admin123)")
    st.stop()

st.markdown('''
<div class="nav-bar">
    <div class="nav-title">⚡ STOCK PORTFOLIO AI & LIVE TERMINAL</div>
    <div class="nav-subtitle">Real-Time Market Analytics, Intelligent Portfolio Manager & Order Book Stream</div>
</div>
''', unsafe_allow_html=True)

st.sidebar.header("⚡ Terminal & Stream Settings")
refresh_rate = st.sidebar.slider("Polling Frequency (Seconds)", min_value=1, max_value=10, value=3)
auto_refresh = st.sidebar.toggle("Live Stream Engine", value=True)
depth_levels = st.sidebar.slider("Depth Grid Levels", min_value=5, max_value=20, value=8)

if auto_refresh:
    count = st_autorefresh(interval=refresh_rate * 1000, key="datarefresh")

st.sidebar.markdown("---")
if st.sidebar.button("🏠 Return to Main Hub", use_container_width=True):
    st.session_state.active_section = "Home Hub"
    st.rerun()

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.active_section = "Home Hub"
    st.rerun()

@st.cache_data(ttl=300)
def fetch_live_price(symbol, fallback_price):
    try:
        ticker_str = f"{symbol}.NS" if not symbol.endswith((".NS", ".BO")) else symbol
        hist = yf.Ticker(ticker_str).history(period="2d")
        if len(hist) >= 2:
            return round(float(hist["Close"].iloc[-1]), 2), round(float(hist["Close"].iloc[-2]), 2)
        elif len(hist) == 1:
            return round(float(hist["Close"].iloc[0]), 2), round(float(hist["Close"].iloc[0]), 2)
    except Exception:
        pass
    return fallback_price, fallback_price

if "portfolio" not in st.session_state:
    st.session_state.portfolio = [
        {"Symbol": "TCS", "Name": "Tata Consultancy Services", "Qty": 10, "Buy_Price": 3500.0},
        {"Symbol": "INFY", "Name": "Infosys Ltd", "Qty": 25, "Buy_Price": 1600.0},
        {"Symbol": "RELIANCE", "Name": "Reliance Industries", "Qty": 15, "Buy_Price": 2800.0},
        {"Symbol": "HDFCBANK", "Name": "HDFC Bank Ltd", "Qty": 20, "Buy_Price": 1500.0}
    ]

if "custom_orders" not in st.session_state:
    st.session_state.custom_orders = {}

portfolio_symbols = [item["Symbol"] for item in st.session_state.portfolio]
selected_symbol = st.sidebar.selectbox("Active Stream Ticker", portfolio_symbols)

if selected_symbol not in st.session_state.custom_orders:
    st.session_state.custom_orders[selected_symbol] = []

portfolio_records = []
for item in st.session_state.portfolio:
    live_p, prev_p = fetch_live_price(item["Symbol"], item.get("Buy_Price", 0.0))
    portfolio_records.append({
        **item,
        "Current_Price": live_p,
        "Yesterday_Close": prev_p
    })

df_portfolio = pd.DataFrame(portfolio_records)
df_portfolio["Total_Cost"] = df_portfolio["Qty"] * df_portfolio["Buy_Price"]
df_portfolio["Current_Value"] = df_portfolio["Qty"] * df_portfolio["Current_Price"]
df_portfolio["P_L"] = df_portfolio["Current_Value"] - df_portfolio["Total_Cost"]
df_portfolio["Return_Pct"] = (df_portfolio["P_L"] / df_portfolio["Total_Cost"]) * 100
df_portfolio["1D_Change_Pct"] = ((df_portfolio["Current_Price"] - df_portfolio["Yesterday_Close"]) / df_portfolio["Yesterday_Close"]) * 100

total_invested = df_portfolio["Total_Cost"].sum()
total_value = df_portfolio["Current_Value"].sum()
total_pnl = df_portfolio["P_L"].sum()
total_return_pct = (total_pnl / total_invested) * 100 if total_invested > 0 else 0

if st.session_state.active_section == "Home Hub":
    st.markdown("<h2 style='text-align: center; color: #f8fafc; margin-bottom: 30px;'>📂 Control Center Menu</h2>", unsafe_allow_html=True)

    row1_c1, row1_c2, row1_c3 = st.columns(3)

    with row1_c1:
        st.markdown('''
        <div class="modern-card" style="padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">💼</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">Portfolio Manager</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;">Manage stock holdings, add investments, and review asset allocation ratios.</p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("Access Portfolio", use_container_width=True, key="btn_portfolio"):
            st.session_state.active_section = "Portfolio"
            st.rerun()

    with row1_c2:
        st.markdown('''
        <div class="modern-card" style="padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">📈</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">Live Stream Analytics</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;">Monitor live pricing trends, moving averages, and technical indicators.</p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("Access Live Stream", use_container_width=True, key="btn_stream"):
            st.session_state.active_section = "Live Stream"
            st.rerun()

    with row1_c3:
        st.markdown('''
        <div class="modern-card" style="padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">📋</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">Order Book & Depth</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;">Inspect market bids/asks, order queues, and cumulative market depth curves.</p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("Access Order Book", use_container_width=True, key="btn_orderbook"):
            st.session_state.active_section = "Order Book"
            st.rerun()

    st.write("")
    row2_c1, row2_c2 = st.columns(2)

    with row2_c1:
        st.markdown('''
        <div class="modern-card" style="padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">👨‍💻</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">Development Team</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;">View project creators, contributors, and data science team info.</p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("View Team Roster", use_container_width=True, key="btn_team"):
            st.session_state.active_section = "Team"
            st.rerun()

    with row2_c2:
        st.markdown('''
        <div class="modern-card" style="padding: 30px 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 10px;">🚪</div>
            <h3 style="color: #ffffff; margin-bottom: 8px;">Logout Session</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 20px;">Safely exit the secure terminal and clear session cache credentials.</p>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("Logout Now", use_container_width=True, key="btn_logout_hub"):
            st.session_state.authenticated = False
            st.session_state.active_section = "Home Hub"
            st.rerun()

elif st.session_state.active_section == "Portfolio":
    if st.button("⬅ Back to Main Hub"):
        st.session_state.active_section = "Home Hub"
        st.rerun()

    st.markdown("## 💼 Intelligent Portfolio Manager")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="modern-card"><div class="card-icon">💼</div><div class="card-title">Total Invested</div><div class="card-value">₹{total_invested:,.2f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="modern-card"><div class="card-icon">📈</div><div class="card-title">Portfolio Value</div><div class="card-value">₹{total_value:,.2f}</div></div>', unsafe_allow_html=True)
    with col3:
        pnl_class = "metric-positive" if total_pnl >= 0 else "metric-negative"
        pnl_sign = "+" if total_pnl >= 0 else ""
        st.markdown(f'<div class="modern-card"><div class="card-icon">🎯</div><div class="card-title">Overall Return</div><div class="card-value {pnl_class}">{pnl_sign}₹{total_pnl:,.2f} ({pnl_sign}{total_return_pct:.2f}%)</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="modern-card"><div class="card-icon">📊</div><div class="card-title">Total Assets</div><div class="card-value">{len(df_portfolio)} Stocks</div></div>', unsafe_allow_html=True)

    st.write("")

    with st.expander("➕ Add New Stock Position / Expand Portfolio", expanded=False):
        with st.form("add_stock_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                in_symbol = st.text_input("Stock Symbol (e.g., TATAMOTORS, SBIN)").strip().upper()
                in_name = st.text_input("Company Name (Optional)")
                in_qty = st.number_input("Quantity", min_value=1, value=10, step=1)
            with f_col2:
                in_buy = st.number_input("Purchase Price (₹)", min_value=0.1, value=500.0, step=10.0)
                st.write("")
                submit_btn = st.form_submit_button("🚀 Add Position")

            if submit_btn and in_symbol:
                existing = next((item for item in st.session_state.portfolio if item["Symbol"] == in_symbol), None)
                if existing:
                    total_qty = existing["Qty"] + int(in_qty)
                    avg_buy = ((existing["Qty"] * existing["Buy_Price"]) + (int(in_qty) * float(in_buy))) / total_qty
                    existing["Qty"] = total_qty
                    existing["Buy_Price"] = round(avg_buy, 2)
                else:
                    st.session_state.portfolio.append({
                        "Symbol": in_symbol,
                        "Name": in_name if in_name else f"{in_symbol} Corp",
                        "Qty": int(in_qty),
                        "Buy_Price": float(in_buy)
                    })
                st.success(f"Added {in_symbol} successfully!")
                st.rerun()

    search_query = st.text_input("🔍 Filter portfolio by Symbol or Name:", "").strip().upper()
    filtered_df = df_portfolio[df_portfolio["Symbol"].str.contains(search_query) | df_portfolio["Name"].str.upper().contains(search_query)] if search_query else df_portfolio

    left_col, right_col = st.columns([1.3, 0.7])
    with left_col:
        st.markdown("### 📊 Holdings Breakdown")
        styled_df = filtered_df[["Symbol", "Name", "Qty", "Buy_Price", "Current_Price", "Total_Cost", "Current_Value", "1D_Change_Pct", "Return_Pct"]].copy()
        styled_df.columns = ["Symbol", "Name", "Qty", "Buy (₹)", "Current (₹)", "Invested (₹)", "Value (₹)", "1D (%)", "Total Return (%)"]
        st.dataframe(
            styled_df.style.format({
                "Buy (₹)": "{:,.2f}",
                "Current (₹)": "{:,.2f}",
                "Invested (₹)": "{:,.2f}",
                "Value (₹)": "{:,.2f}",
                "1D (%)": "{:+.2f}%",
                "Total Return (%)": "{:+.2f}%"
            }),
            use_container_width=True,
            height=330
        )

    with right_col:
        st.markdown("### 🥧 Asset Allocation")
        fig_pie = px.pie(df_portfolio, values="Current_Value", names="Symbol", hole=0.5, color_discrete_sequence=["#6366f1", "#8b5cf6", "#3b82f6", "#06b6d4", "#10b981"])
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

elif st.session_state.active_section == "Live Stream":
    if st.button("⬅ Back to Main Hub"):
        st.session_state.active_section = "Home Hub"
        st.rerun()

    base_fallback_price = float(df_portfolio[df_portfolio["Symbol"] == selected_symbol]["Current_Price"].values[0]) if not df_portfolio[df_portfolio["Symbol"] == selected_symbol].empty else 1500.0

    if "price_history" not in st.session_state or st.session_state.get("active_symbol") != selected_symbol:
        st.session_state.active_symbol = selected_symbol
        now = datetime.now()
        times = [now - timedelta(seconds=i*3) for i in range(40, -1, -1)]
        prices = [base_fallback_price + np.cumsum(np.random.normal(0, 0.5, 41))[i] for i in range(41)]
        st.session_state.price_history = pd.DataFrame({"Timestamp": times, "Price": prices})

    last_price = st.session_state.price_history["Price"].iloc[-1]
    drift = np.random.normal(0.05, 0.4)
    new_price = round(last_price + drift, 2)
    new_time = datetime.now()

    new_row = pd.DataFrame([{"Timestamp": new_time, "Price": new_price}])
    st.session_state.price_history = pd.concat([st.session_state.price_history.iloc[1:], new_row], ignore_index=True)

    df_stream = st.session_state.price_history
    current_p = df_stream["Price"].iloc[-1]
    initial_p = df_stream["Price"].iloc[0]
    pct_change = ((current_p - initial_p) / initial_p) * 100
    delta_p = current_p - df_stream["Price"].iloc[-2]

    st.subheader(f"⚡ Live Streaming Analytics: {selected_symbol}")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        delta_class = "up-tick" if delta_p >= 0 else "down-tick"
        st.markdown(f'''<div class="modern-card"><div class="card-title">{selected_symbol} Live Price</div><div class="card-value {delta_class}">₹{current_p:,.2f}</div></div>''', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'''<div class="modern-card"><div class="card-title">Session Return</div><div class="card-value {delta_class}">{pct_change:+.2f}%</div></div>''', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'''<div class="modern-card"><div class="card-title">24h High</div><div class="card-value">₹{df_stream["Price"].max():,.2f}</div></div>''', unsafe_allow_html=True)
    with m_col4:
        user_orders_count = len(st.session_state.custom_orders[selected_symbol])
        st.markdown(f'''<div class="modern-card"><div class="card-title">Injected Orders</div><div class="card-value">{user_orders_count} Active</div></div>''', unsafe_allow_html=True)

    st.write("")

    df_stream["SMA_10"] = df_stream["Price"].rolling(window=10).mean()
    df_stream["STD_10"] = df_stream["Price"].rolling(window=10).std()
    df_stream["Upper"] = df_stream["SMA_10"] + (df_stream["STD_10"] * 2)
    df_stream["Lower"] = df_stream["SMA_10"] - (df_stream["STD_10"] * 2)

    fig_stream = go.Figure()
    fig_stream.add_trace(go.Scatter(x=df_stream["Timestamp"], y=df_stream["Price"], mode="lines+markers", name="Price", line=dict(color="#6366f1", width=2.5)))
    fig_stream.add_trace(go.Scatter(x=df_stream["Timestamp"], y=df_stream["Upper"], mode="lines", name="Upper Band", line=dict(color="rgba(148, 163, 184, 0.3)", dash="dot")))
    fig_stream.add_trace(go.Scatter(x=df_stream["Timestamp"], y=df_stream["Lower"], mode="lines", name="Lower Band", line=dict(color="rgba(148, 163, 184, 0.3)", dash="dot"), fill="tonexty", fillcolor="rgba(99, 102, 241, 0.05)"))
    fig_stream.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(19, 27, 46, 0.5)", margin=dict(l=10, r=10, t=20, b=10), height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    components.html(fig_stream.to_html(include_plotlyjs="cdn", full_html=False), height=420)

elif st.session_state.active_section == "Order Book":
    if st.button("⬅ Back to Main Hub"):
        st.session_state.active_section = "Home Hub"
        st.rerun()

    base_fallback_price = float(df_portfolio[df_portfolio["Symbol"] == selected_symbol]["Current_Price"].values[0]) if not df_portfolio[df_portfolio["Symbol"] == selected_symbol].empty else 1500.0

    if "price_history" in st.session_state and not st.session_state.price_history.empty:
        current_p = st.session_state.price_history["Price"].iloc[-1]
    else:
        current_p = base_fallback_price

    st.subheader(f"⚡ Order Book & Market Depth ({selected_symbol})")

    with st.expander(f"📥 Place Custom Order in {selected_symbol}", expanded=True):
        with st.form("place_order_form", clear_on_submit=True):
            o_col1, o_col2, o_col3 = st.columns(3)
            with o_col1:
                side = st.selectbox("Side", ["BUY (Bid)", "SELL (Ask)"])
            with o_col2:
                order_qty = st.number_input("Quantity (Shares)", min_value=1, value=50, step=10)
            with o_col3:
                order_price = st.number_input("Target Price (₹)", min_value=0.1, value=float(round(current_p, 2)), step=0.5)

            place_btn = st.form_submit_button("🚀 Inject into Order Book", use_container_width=True)

            if place_btn:
                order_type = "BUY" if "BUY" in side else "SELL"
                st.session_state.custom_orders[selected_symbol].append({
                    "type": order_type,
                    "price": round(order_price, 2),
                    "qty": int(order_qty)
                })
                st.success(f"Injected {order_type} {order_qty}x @ ₹{order_price:.2f}")

    if st.button("🧹 Clear Injected Custom Orders"):
        st.session_state.custom_orders[selected_symbol] = []
        st.rerun()

    np.random.seed(int(time.time() * 10) % 1000)
    tick_step = 0.25

    bid_prices = [round(current_p - i * tick_step, 2) for i in range(1, depth_levels + 1)]
    ask_prices = [round(current_p + i * tick_step, 2) for i in range(1, depth_levels + 1)]
    bid_vols = list(np.random.randint(20, 250, size=depth_levels))
    ask_vols = list(np.random.randint(20, 250, size=depth_levels))

    for custom_ord in st.session_state.custom_orders[selected_symbol]:
        p = custom_ord["price"]
        q = custom_ord["qty"]
        if custom_ord["type"] == "BUY":
            if p in bid_prices:
                bid_vols[bid_prices.index(p)] += q
            else:
                bid_prices.append(p); bid_vols.append(q)
        elif custom_ord["type"] == "SELL":
            if p in ask_prices:
                ask_vols[ask_prices.index(p)] += q
            else:
                ask_prices.append(p); ask_vols.append(q)

    bids_combined = sorted(zip(bid_prices, bid_vols), key=lambda x: x[0], reverse=True)[:depth_levels]
    asks_combined = sorted(zip(ask_prices, ask_vols), key=lambda x: x[0])[:depth_levels]

    final_bid_p = [b[0] for b in bids_combined]
    final_bid_q = [b[1] for b in bids_combined]
    final_ask_p = [a[0] for a in asks_combined]
    final_ask_q = [a[1] for a in asks_combined]

    min_len = min(len(final_bid_p), len(final_ask_p))
    order_df = pd.DataFrame({"Bid Qty": final_bid_q[:min_len], "Bid Price (₹)": final_bid_p[:min_len], "Ask Price (₹)": final_ask_p[:min_len], "Ask Qty": final_ask_q[:min_len]})

    depth_col1, depth_col2 = st.columns([1, 1])
    with depth_col1:
        st.markdown("##### 📋 Order Depth Table")
        st.dataframe(order_df.style.background_gradient(subset=["Bid Qty"], cmap="Greens").background_gradient(subset=["Ask Qty"], cmap="Reds"), use_container_width=True, height=320)

    with depth_col2:
        st.markdown("##### 🌊 Cumulative Depth Curve")
        depth_fig = go.Figure()
        depth_fig.add_trace(go.Scatter(
            x=final_bid_p[::-1],
            y=np.cumsum(final_bid_q)[::-1],
            mode="lines",
            name="Bids",
            line=dict(color="#10b981", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(16, 185, 129, 0.15)"
        ))
        depth_fig.add_trace(go.Scatter(
            x=final_ask_p,
            y=np.cumsum(final_ask_q),
            mode="lines",
            name="Asks",
            line=dict(color="#f43f5e", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(244, 63, 94, 0.15)"
        ))
        depth_fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(19, 27, 46, 0.5)", margin=dict(l=10, r=10, t=10, b=10), height=300, showlegend=True, xaxis_title="Price (₹)", yaxis_title="Cumulative Volume")
        components.html(depth_fig.to_html(include_plotlyjs="cdn", full_html=False), height=320)

elif st.session_state.active_section == "Team":
    if st.button("⬅ Back to Main Hub"):
        st.session_state.active_section = "Home Hub"
        st.rerun()

    st.markdown("<h3 style='text-align: center; margin-bottom: 25px;'>👨‍💻 Project Developer</h3>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 1.2, 1])

    with col_center:
        st.markdown('<div class="team-card"><img class="team-avatar" src="https://api.dicebear.com/7.x/bottts/svg?seed=Om"/><div class="team-name">Om Todmal</div><div class="team-role">Data Science</div><span class="team-badge">Data Science</span></div>', unsafe_allow_html=True)
"""

with open("app.py", "w") as f:
    f.write(app_code)

os.system("pkill -9 -f streamlit")
os.system("pkill -9 -f cloudflared")
time.sleep(1)

if os.path.exists("tunnel.log"):
    os.remove("tunnel.log")

os.system(f"nohup {sys.executable} -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false > streamlit.log 2>&1 &")
time.sleep(3)

os.system("nohup ./cloudflared tunnel --url http://127.0.0.1:8501 > tunnel.log 2>&1 &")

print("Launching Secure Live Terminal with Login & Team Roster...")
tunnel_url = None

for _ in range(40):
    time.sleep(0.5)
    if os.path.exists("tunnel.log"):
        with open("tunnel.log", "r") as f:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", f.read())
            if match:
                tunnel_url = match.group(0)
                break

if tunnel_url:
    print(f"Tunnel generated: {tunnel_url}")
    for _ in range(15):
        try:
            res = requests.get(tunnel_url, timeout=3)
            if res.status_code == 200:
                print(f"\nReady and Verified LIVE:\n{tunnel_url}\n")
                break
        except requests.RequestException:
            pass
        time.sleep(1)
