import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf

st.title("Pocket Option 3M Strategy - Signals Bot")

# اختيار الزوج والمدخلات
symbol = st.selectbox("اختر زوج العملات:", ["EURUSD=X", "GBPUSD=X", "USDJPY=X"])
df = yf.download(symbol, period="1d", interval="1m")

if not df.empty:
    # إصلاح هيكل البيانات إذا كان MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # حساب المؤشرات
    df['EMA_9'] = ta.ema(df['Close'], length=9)
    df['EMA_21'] = ta.ema(df['Close'], length=21)
    df['RSI_14'] = ta.rsi(df['Close'], length=14)

    # تحديد شروط الصفقات
    df['Signal'] = "محياد"
    
    # شرط الشراء (CALL)
    buy_cond = (df['EMA_9'] > df['EMA_21']) & (df['EMA_9'].shift(1) <= df['EMA_21'].shift(1)) & (df['RSI_14'] > 50)
    # شرط البيع (PUT)
    sell_cond = (df['EMA_9'] < df['EMA_21']) & (df['EMA_9'].shift(1) >= df['EMA_21'].shift(1)) & (df['RSI_14'] < 50)

    df.loc[buy_cond, 'Signal'] = "🟢 شراء (CALL 3M)"
    df.loc[sell_cond, 'Signal'] = "🔴 بيع (PUT 3M)"

    # عرض آخر شمعة والإشارة الحالية
    latest = df.iloc[-1]
    st.metric(label="السعر الحالي", value=f"{latest['Close']:.5f}")
    st.subheader(f"الحالة الحالية: {latest['Signal']}")

    # عرض جدول أحدث البيانات
    st.dataframe(df[['Close', 'EMA_9', 'EMA_21', 'RSI_14', 'Signal']].tail(10))
          
