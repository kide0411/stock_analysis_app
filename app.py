import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AI股票智能分析師", layout="wide")
st.title("AI智能股票分析師")

# ---------------------------
# 股票輸入
# ---------------------------
stock_code = st.text_input("股票代號 (例如: 2330.TW)", value="2330.TW")

# ---------------------------
# 抓取股票資料
# ---------------------------
@st.cache_data
def fetch_stock_data(ticker):
    data = yf.download(ticker, period="180d", interval="1d")
    data['MA5'] = data['Close'].rolling(5).mean()
    data['MA20'] = data['Close'].rolling(20).mean()
    data['STD20'] = data['Close'].rolling(20).std()
    data['UpperBB'] = data['MA20'] + 2 * data['STD20']
    data['LowerBB'] = data['MA20'] - 2 * data['STD20']
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1*delta.clip(upper=0)
    roll_up = up.rolling(14).mean()
    roll_down = down.rolling(14).mean()
    data['RSI'] = 100 - 100 / (1 + roll_up / roll_down)
    # MACD
    data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    return data

try:
    stock_data = fetch_stock_data(stock_code)
    current_price = stock_data['Close'].iloc[-1]
    st.write(f"最新收盤價: {current_price:.2f}")
except:
    st.error("無法抓取股票資料，請確認代碼或網路。")
    st.stop()

# ---------------------------
# 法人籌碼分析
# ---------------------------
st.subheader("法人籌碼分析")
url = f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=html&date=20250821&selectType=ALLBUT0999"
try:
    response = requests.get(url)
    data_chip = pd.read_html(response.text)[0]
    data_chip.columns = data_chip.iloc[0]
    data_chip = data_chip.drop(0)
    data_chip = data_chip.set_index('證券代號')
    stock_chips = data_chip.loc[stock_code]
    foreign_net = int(stock_chips['外資買超股數'])
    invest_trust_net = int(stock_chips['投信買超股數'])
    dealer_net = int(stock_chips['自營商買超股數'])
    st.write(f"外資買超股數: {foreign_net}")
    st.write(f"投信買超股數: {invest_trust_net}")
    st.write(f"自營商買超股數: {dealer_net}")
except:
    st.warning("無法抓取法人籌碼資料，可手動輸入")
    foreign_net = st.number_input("外資買賣超(張)", value=0)
    invest_trust_net = st.number_input("投信買賣超(張)", value=0)
    dealer_net = st.number_input("自營商買賣超(張)", value=0)

# ---------------------------
# 技術面分析
# ---------------------------
st.subheader("技術面分析")
latest = stock_data.iloc[-1]
ma5, ma20, rsi = latest['MA5'], latest['MA20'], latest['RSI']

tech_score = 0
tech_msgs = []

# 均線判斷
if current_price > ma5 and current_price > ma20:
    tech_score += 2
    tech_msgs.append("股價高於MA5及MA20，短中期偏多。")
else:
    tech_score -= 2
    tech_msgs.append("股價低於均線，偏空。")

# RSI判斷
if rsi < 30:
    tech_score += 1
    tech_msgs.append("RSI低於30，短線超賣偏多。")
elif rsi > 70:
    tech_score -=1
    tech_msgs.append("RSI高於70，短線超買偏空。")

# ---------------------------
# 籌碼面分析
# ---------------------------
chip_score = 0
chip_msgs = []

net_total = foreign_net + invest_trust_net + dealer_net
if net_total > 0:
    chip_score +=1
    chip_msgs.append("法人總買超，偏多。")
elif net_total < 0:
    chip_score -=1
    chip_msgs.append("法人總賣超，偏空。")
else:
    chip_msgs.append("法人買賣超平衡，無偏向。")

# ---------------------------
# 大盤與期貨分析
# ---------------------------
st.subheader("大盤與期貨分析")
try:
    twii = yf.Ticker("^TWII")
    twii_hist = twii.history(period="60d")
    taiwan_index = twii_hist['Close'].iloc[-1]
    st.write(f"加權指數收盤價: {taiwan_index}")
except:
    st.warning("無法抓取大盤資料，可手動輸入")
    taiwan_index = st.number_input("加權指數收盤價", value=0)

# ---------------------------
# 綜合判斷
# ---------------------------
total_score = tech_score + chip_score

if total_score > 2:
    direction = "多方偏強"
    win_rate = 70
elif total_score > 0:
    direction = "偏多"
    win_rate = 60
elif total_score == 0:
    direction = "中立"
    win_rate = 50
elif total_score > -2:
    direction = "偏空"
    win_rate = 40
else:
    direction = "空方偏強"
    win_rate = 30

# ---------------------------
# 結果顯示
# ---------------------------
st.subheader("分析結果")
st.markdown(f"**判斷方向:** {direction}")
st.markdown(f"**勝率估算:** {win_rate}%")

st.markdown("**詳細分析文字解讀:**")
for msg in tech_msgs + chip_msgs:
    st.write(f"- {msg}")

st.markdown("**操作建議:**")
if direction in ["多方偏強", "偏多"]:
    st.write("- 可考慮逢低買進或持有，注意支撐位與停損點。")
elif direction in ["偏空", "空方偏強"]:
    st.write("- 可考慮觀望或減碼，若持股建議設停損。")
else:
    st.write("- 建議觀望，等待明確趨勢訊號。")

# ---------------------------
# 互動技術圖表
# ---------------------------
st.subheader("互動技術圖表")
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.02, 
                    row_heights=[0.7,0.3], 
                    specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

# K線 + 均線 + 布林帶
fig.add_trace(go.Candlestick(x=stock_data.index,
                             open=stock_data['Open'],
                             high=stock_data['High'],
                             low=stock_data['Low'],
                             close=stock_data['Close'],
                             name="K線"))
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA5'], line=dict(color='blue', width=1), name='MA5'))
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA20'], line=dict(color='orange', width=1), name='MA20'))
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['UpperBB'], line=dict(color='lightgray', width=1), name='UpperBB'))
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['LowerBB'], line=dict(color='lightgray', width=1), name='LowerBB'))

# 成交量
fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='成交量', marker_color='gray'), row=2, col=1)

# MACD 與 Signal
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MACD'], line=dict(color='green', width=1), name='MACD'), row=1, col=1, secondary_y=True)
fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Signal'], line=dict(color='red', width=1), name='Signal'), row=1, col=1, secondary_y=True)

# 更新 layout
fig.update_layout(xaxis_rangeslider_visible=False, height=700, width=1000)
st.plotly_chart(fig, use_container_width=True)
