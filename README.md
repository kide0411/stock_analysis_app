# AI智能股票分析師 (Stock Analysis AI)

本專案是一個基於 **Streamlit** 的 AI 股票分析師應用，結合技術面、籌碼面、大盤資料與互動圖表，提供股票操作方向、勝率估算與操作建議。

---

## 功能特色

1. 股票資料抓取：支援台股代號 (例如：`2330.TW`)，抓取最近 180 日歷史股價，計算技術指標：MA5、MA20、布林通道、RSI、MACD。
2. 法人籌碼分析：顯示外資、投信、自營商買賣超，可手動輸入籌碼資料。
3. 大盤與期貨分析：顯示加權指數收盤價，可手動輸入。
4. 技術面 + 籌碼面分析：均線、RSI 判斷多空，法人總買賣超偏多或偏空。
5. 操作建議：綜合技術面、籌碼面、大盤，提供買進、持有、觀望或減碼建議。
6. 互動技術圖表：K 線圖、均線、布林帶、成交量、MACD 與 Signal 線，可放大縮小、懸停查看數據。

---

## 系統需求

- Python 3.10 ~ 3.13
- 作業系統：Windows / MacOS / Linux
- 建議使用虛擬環境（venv 或 conda）

---

## 安裝與執行

```bash
git clone https://github.com/<你的帳號>/stock_analysis_app.git
cd stock_analysis_app
pip install -r requirements.txt
streamlit run app.py
