import streamlit as st
import pandas as pd
import yfinance as yf
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

st.set_page_config(page_title="Pocket Option Signals", layout="wide")
st.title("📊 Pocket Option 3M Strategy Bot")

# اختيار الزوج
symbol = st.selectbox("اختر زوج العملات:", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "GBPJPY=X"])

# جلب بيانات دقيقة واحدة
df = yf.download(symbol, period="1d", interval="1m")

if not df.empty:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # حساب المؤشرات
    df['EMA_9'] = EMAIndicator(close=df['Close'], window=9).ema_indicator()
    df['EMA_21'] = EMAIndicator(close=df['Close'], window=21).ema_indicator()
    df['RSI_14'] = RSIIndicator(close=df['Close'], window=14).rsi()

    # تحديد شروط التقاطع
    buy_cond = (df['EMA_9'] > df['EMA_21']) & (df['EMA_9'].shift(1) <= df['EMA_21'].shift(1)) & (df['RSI_14'] > 50)
    sell_cond = (df['EMA_9'] < df['EMA_21']) & (df['EMA_9'].shift(1) >= df['EMA_21'].shift(1)) & (df['RSI_14'] < 50)

    df['Signal'] = "محايد ⚪"
    df.loc[buy_cond, 'Signal'] = "🟢 شراء (CALL) - مدة 3 دقائق"
    df.loc[sell_cond, 'Signal'] = "🔴 بيع (PUT) - مدة 3 دقائق"

    # تصفية الصفقات فقط
    signals_df = df[df['Signal'] != "محايد ⚪"]

    # عرض حالة السوق الحالية
    latest = df.iloc[-1]
    st.metric(label="السعر الحالي", value=f"{latest['Close']:.5f}")

    if latest['Signal'] != "محايد ⚪":
        st.success(f"🚨 **إشارة جديدة الآن!** {latest['Signal']}")
    else:
        st.info("⏳ السوق في حالة انتظار.. لا توجد إشارة تقاطع في الشمعة الحالية.")

    st.markdown("---")
    st.subheader("⏱️ آخر الإشارات الصادرة ووقت دخولها:")

    if not signals_df.empty:
        # عرض آخر 5 إشارات حدثت مع الوقت والتاريخ
        last_signals = signals_df[['Close', 'EMA_9', 'EMA_21', 'RSI_14', 'Signal']].tail(5)
        st.dataframe(last_signals)
    else:
        st.write("لم تظهر أي إشارات في الساعات الأخيرة على هذا الزوج.")
        
