import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="AI 股票分析師", layout="wide")

st.title("AI 智能股票分析師")

# --- 股票輸入 ---
ticker = st.text_input("輸入台股代號 (加 .TW):", value="2330.TW")

# --- 抓取歷史資料 ---
if ticker:
    try:
        data = yf.download(ticker, period="180d", interval="1d", threads=False, progress=False)
    except Exception as e:
        st.error(f"抓取資料時發生錯誤: {e}")
        data = pd.DataFrame()

    if not data.empty:
        st.subheader("歷史股價 (最近5日)")
        st.dataframe(data.tail(5))

        # --- 技術指標計算 ---
        data['MA5'] = data['Close'].rolling(5).mean()
        data['MA20'] = data['Close'].rolling(20).mean()
        data['STD'] = data['Close'].rolling(20).std()
        data['Upper'] = data['MA20'] + 2 * data['STD']
        data['Lower'] = data['MA20'] - 2 * data['STD']

        delta = data['Close'].diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        data['RSI'] = 100 - 100 / (1 + roll_up / roll_down)

        exp12 = data['Close'].ewm(span=12, adjust=False).mean()
        exp26 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp12 - exp26
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

        # --- K 線圖 ---
        st.subheader("互動技術圖表")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="K線"
        ))
        fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], line=dict(color='blue', width=1), name='MA5'))
        fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], line=dict(color='red', width=1), name='MA20'))
        fig.add_trace(go.Scatter(x=data.index, y=data['Upper'], line=dict(color='gray', width=1, dash='dash'), name='Upper BB'))
        fig.add_trace(go.Scatter(x=data.index, y=data['Lower'], line=dict(color='gray', width=1, dash='dash'), name='Lower BB'))
        st.plotly_chart(fig, use_container_width=True)

        # --- 成交量 & MACD ---
        st.subheader("成交量 & MACD")
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=data.index, y=data['Volume'], name='成交量'))
        fig2.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='orange', width=2), name='MACD'))
        fig2.add_trace(go.Scatter(x=data.index, y=data['Signal'], line=dict(color='purple', width=2), name='Signal'))
        st.plotly_chart(fig2, use_container_width=True)

        # --- 籌碼面手動輸入 ---
        st.subheader("法人籌碼分析 (手動輸入)")
        foreign = st.number_input("外資買賣超", value=0)
        investment = st.number_input("投信買賣超", value=0)
        dealer = st.number_input("自營商買賣超", value=0)
        total_chip = foreign + investment + dealer

        # --- 技術面與籌碼面分析 ---
        st.subheader("技術面 + 籌碼面分析")
        tech_signal = "多方" if data['Close'].iloc[-1] > data['MA20'].iloc[-1] else "空方"
        chip_signal = "偏多" if total_chip > 0 else "偏空"
        st.write(f"技術面判斷: {tech_signal}")
        st.write(f"籌碼面判斷: {chip_signal}")

        # --- 操作建議 ---
        st.subheader("操作建議")
        if tech_signal == "多方" and chip_signal == "偏多":
            advice = "建議買進或持有"
        elif tech_signal == "空方" and chip_signal == "偏空":
            advice = "建議減碼或觀望"
        else:
            advice = "建議觀察盤勢"
        st.success(advice)

    else:
        st.error("無法抓取股票資料，請確認代號是否正確或稍後再試")
