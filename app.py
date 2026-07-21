import streamlit as st
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

# ضبط تصميم الصفحة
st.set_page_config(page_title="Pocket Option - 3M Signals", layout="centered")

st.title("🎯 بوت إشارات Pocket Option (3 دقائق)")

# اختيار الزوج
symbol = st.selectbox("اختر زوج العملات:", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GBPJPY=X"])

# زر لتحديث البيانات يدويًا فورًا
if st.button("🔄 تحديث الإشارة الآن"):
    st.rerun()

# جلب البيانات
df = yf.download(symbol, period="1d", interval="1m")

if not df.empty:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # حساب المؤشرات
    df['EMA_9'] = EMAIndicator(close=df['Close'], window=9).ema_indicator()
    df['EMA_21'] = EMAIndicator(close=df['Close'], window=21).ema_indicator()
    df['RSI_14'] = RSIIndicator(close=df['Close'], window=14).rsi()

    # فحص آخر شمعة مكتملة (الشمعة السابقة فورًا)
    last_row = df.iloc[-2]
    prev_row = df.iloc[-3]

    # شروط التقاطع
    buy_cond = (last_row['EMA_9'] > last_row['EMA_21']) and (prev_row['EMA_9'] <= prev_row['EMA_21']) and (last_row['RSI_14'] > 50)
    sell_cond = (last_row['EMA_9'] < last_row['EMA_21']) and (prev_row['EMA_9'] >= prev_row['EMA_21']) and (last_row['RSI_14'] < 50)

    st.markdown("---")
    st.subheader("📢 القرار الحالي للشمعة الحالية:")

    # عرض النتيجة ببطاقة ملونة واضحة جداً
    if buy_cond:
        st.success("🟢 **ادخل صفقة شراء (CALL / HIGHER) الآن!**\n\n⏰ المدة: **3 دقائق** على Pocket Option.")
    elif sell_cond:
        st.error("🔴 **ادخل صفقة بيع (PUT / LOWER) الآن!**\n\n⏰ المدة: **3 دقائق** على Pocket Option.")
    else:
        st.info("⏳ **انتظر (لا توجد إشارة دخول الآن)**\n\nتأكد من الضغط على زر التحديث كل دقيقة عند إغلاق الشمعة.")

    st.markdown("---")
    st.write(f"📊 **السعر الحالي:** {df.iloc[-1]['Close']:.5f}")
