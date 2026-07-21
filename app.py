import streamlit as st
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

st.set_page_config(page_title="Pocket Option Signals", layout="wide")
st.title("📊 Pocket Option 3M Strategy Bot")

# اختيار الزوج
symbol = st.selectbox("اختر زوج العملات:", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GBPJPY=X"])

# جلب البيانات
df = yf.download(symbol, period="1d", interval="1m")

if not df.empty:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 1. حساب المتوسطات المتحركة EMA
    df['EMA_9'] = EMAIndicator(close=df['Close'], window=9).ema_indicator()
    df['EMA_21'] = EMAIndicator(close=df['Close'], window=21).ema_indicator()

    # 2. حساب مؤشر القوة النسبية RSI
    df['RSI_14'] = RSIIndicator(close=df['Close'], window=14).rsi()

    # 3. تحديث شروط الصفقات
    df['Signal'] = "محايد ⚪"
    
    # شروط الشراء والبيع
    buy_cond = (df['EMA_9'] > df['EMA_21']) & (df['EMA_9'].shift(1) <= df['EMA_21'].shift(1)) & (df['RSI_14'] > 50)
    sell_cond = (df['EMA_9'] < df['EMA_21']) & (df['EMA_9'].shift(1) >= df['EMA_21'].shift(1)) & (df['RSI_14'] < 50)

    df.loc[buy_cond, 'Signal'] = "🟢 شراء (CALL 3M)"
    df.loc[sell_cond, 'Signal'] = "🔴 بيع (PUT 3M)"

    # عرض النتيجة للحالة الحالية
    latest = df.iloc[-1]
    st.metric(label="السعر الحالي", value=f"{latest['Close']:.5f}")
    st.subheader(f"التوصية الحالية: {latest['Signal']}")

    # عرض جدول أحدث البيانات
    st.dataframe(df[['Close', 'EMA_9', 'EMA_21', 'RSI_14', 'Signal']].tail(10))
