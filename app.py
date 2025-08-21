import streamlit as st
st.title("升級版股票數據分析與策略建議")
st.write("將完整升級版程式碼貼在這裡")
import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="價格區間模擬交易計算", layout="wide")

st.title("價格區間模擬交易計算")

# --- 輸入參數 ---
trade_type = st.selectbox("交易類型", ["當沖", "非當沖"])
trade_direction = st.selectbox("交易方向", ["做多", "做空"])
buy_price = st.number_input("買入價格 / 賣出價格", min_value=0.01, value=100.0, format="%.2f")
shares = st.number_input("股數", min_value=1, value=1000)
fee_discount = st.number_input("手續費折數（預設2.8折）", min_value=0.1, max_value=10.0, value=2.8, format="%.2f")

# --- 計算股價跳動單位 ---
def get_tick_unit(price):
    if price < 10:
        return 0.01
    elif 10 <= price < 50:
        return 0.05
    elif 50 <= price < 100:
        return 0.1
    elif 100 <= price < 500:
        return 0.5
    elif 500 <= price < 1000:
        return 1
    else:
        return 5

# --- 初始價格範圍 ---
if "base_prices" not in st.session_state:
    tick = get_tick_unit(buy_price)
    st.session_state.base_prices = [round(buy_price + i * tick, 2) for i in range(1, 6)] + \
                                   [round(buy_price - i * tick, 2) for i in range(5, 0, -1)]
if "price_step" not in st.session_state:
    st.session_state.price_step = get_tick_unit(buy_price)

# --- 計算獲利 ---
def calculate_profit(b_price, s_price, shares, fee_discount, trade_type, trade_direction):
    fee_rate = 0.001425
    tax_rate = 0.0015 if trade_type == "當沖" else 0.003
    buy_amount = b_price * shares
    sell_amount = s_price * shares
    fee = max(math.floor((buy_amount + sell_amount) * fee_rate * (fee_discount / 10)), 20)
    tax = math.floor((sell_amount if trade_direction == "做多" else buy_amount) * tax_rate)
    profit = sell_amount - buy_amount - fee - tax if trade_direction == "做多" else buy_amount - sell_amount - fee - tax
    roi = round((profit / buy_amount) * 100, 2)
    return fee, tax, profit, roi

# --- 生成表格 ---
def generate_table(base_prices):
    data = []
    for s_price in base_prices:
        fee, tax, profit, roi = calculate_profit(buy_price, s_price, shares, fee_discount, trade_type, trade_direction)
        data.append([buy_price, s_price, tax, fee, profit, f"{roi}%"])
    df = pd.DataFrame(data, columns=["買入價格","賣出價格","證交稅","總手續費","獲利","報酬率"])
    df = df.sort_values("賣出價格", ascending=True).reset_index(drop=True)
    return df

df = generate_table(st.session_state.base_prices)

# --- 顯示表格 ---
st.subheader("價格區間模擬結果")
st.dataframe(df, use_container_width=True)

# --- 延伸按鈕 ---
col1, col2 = st.columns([1,1])
with col1:
    if st.button("顯示更多價格", key="down"):
        last_min = min(st.session_state.base_prices)
        tick = get_tick_unit(last_min)
        new_prices = [round(last_min - i * tick, 2) for i in range(5, 0, -1)]
        st.session_state.base_prices = new_prices + st.session_state.base_prices
        st.experimental_rerun()
with col2:
    if st.button("顯示更多價格", key="up"):
        last_max = max(st.session_state.base_prices)
        tick = get_tick_unit(last_max)
        new_prices = [round(last_max + i * tick, 2) for i in range(1,6)]
        st.session_state.base_prices.extend(new_prices)
        st.experimental_rerun()
