# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="AI股票分析師", layout="wide")

# ---------------------------------
# 標題與說明
# ---------------------------------
st.title("AI智能股票分析師")
st.markdown("""
這是一個使用 **Streamlit** 與 **Python** 打造的 AI 股票分析工具，
能自動抓取個股歷史資料、法人籌碼、技術指標及大盤資訊，
提供智能操作建議、方向判斷與勝率估算。
""")

# ---------------------------------
# 輸入股票代碼
# ---------------------------------
ticker_input = st.text_input("請輸入股票代碼（例如 2330.TW）", value="2330.TW")

# 下載歷史股價
@st.cache_data
def get_stock_data(ticker):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 近一年資料
    data = yf.download(ticker, start=start_date, end=end_date)
    data.reset_index(inplace=True)
    data['MA5'] = data['Close'].rolling(5).mean()
    data['MA20'] = data['Close'].rolling(20).mean()
    # 布林帶
    data['BB_upper'] = data['MA20'] + 2 * data['Close'].rolling(20).std()
    data['BB_lower'] = data['MA20'] - 2 * data['Close'].rolling(20).std()
    # RSI
    delta = data['Close'].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    roll_up = up.rolling(14).mean()
    roll_down = down.abs().rolling(14).mean()
    RS = roll_up / roll_down
    data['RSI'] = 100 - (100 / (1 + RS))
    # MACD
    EMA12 = data['Close'].ewm(span=12, adjust=False).mean()
    EMA26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = EMA12 - EMA26
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    return data

if ticker_input:
    try:
        df = get_stock_data(ticker_input)
        st.subheader(f"{ticker_input} 股價資料 (近一年)")
        st.dataframe(df.tail(10))

        # ---------------------------------
        # 繪製 K 線圖 + 技術指標
        # ---------------------------------
        st.subheader("K線圖與技術指標")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df['Date'],
                                     open=df['Open'],
                                     high=df['High'],
                                     low=df['Low'],
                                     close=df['Close'],
                                     name='K線'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['MA5'], line=dict(color='blue', width=1), name='MA5'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], line=dict(color='orange', width=1), name='MA20'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_upper'], line=dict(color='green', width=1, dash='dot'), name='BB上軌'))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_lower'], line=dict(color='red', width=1, dash='dot'), name='BB下軌'))
        fig.update_layout(xaxis_rangeslider_visible=False, height=600)
        st.plotly_chart(fig, use_container_width=True)

        # 成交量
        st.subheader("成交量")
        vol_fig = go.Figure()
        vol_fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='成交量'))
        st.plotly_chart(vol_fig, use_container_width=True)

        # MACD
        st.subheader("MACD")
        macd_fig = go.Figure()
        macd_fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD'))
        macd_fig.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], name='Signal'))
        st.plotly_chart(macd_fig, use_container_width=True)

        # RSI
        st.subheader("RSI 指標")
        st.line_chart(df[['RSI']].set_index(df['Date']))

        # ---------------------------------
        # 法人籌碼輸入與分析
        # ---------------------------------
        st.subheader("法人籌碼分析")
        st.markdown("請輸入最近一天的買賣超股數（單位：張）")
        col1, col2, col3 = st.columns(3)
        with col1:
            foreign = st.number_input("外資買賣超", value=0)
        with col2:
            investment = st.number_input("投信買賣超", value=0)
        with col3:
            dealer = st.number_input("自營商買賣超", value=0)

        total_chip = foreign + investment + dealer
        if total_chip > 0:
            bias = "偏多"
        elif total_chip < 0:
            bias = "偏空"
        else:
            bias = "中性"
        st.write(f"法人總買賣超: {total_chip} 張 → 市場偏向：{bias}")

        # ---------------------------------
        # 勝率估算與操作建議
        # ---------------------------------
        st.subheader("勝率估算與操作建議")
        last_close = df['Close'].iloc[-1]
        last_rsi = df['RSI'].iloc[-1]

        # 簡單勝率估算：RSI + MA 趨勢
        win_rate = 50
        if last_rsi < 30:
            win_rate += 20
        elif last_rsi > 70:
            win_rate -= 20
        if df['MA5'].iloc[-1] > df['MA20'].iloc[-1]:
            win_rate += 10
        else:
            win_rate -= 10
        win_rate = max(0, min(win_rate, 100))
        st.write(f"預估勝率: {win_rate}%")

        # 操作建議
        if win_rate >= 60 and bias=="偏多":
            suggestion = "建議：可考慮買進或持有"
        elif win_rate <= 40 and bias=="偏空":
            suggestion = "建議：可考慮賣出或觀望"
        else:
            suggestion = "建議：觀望為主"
        st.write(suggestion)

    except Exception as e:
        st.error(f"發生錯誤: {e}")
