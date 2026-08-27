import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta

# ==========================================
# 1. إعدادات الصفحة والتصاميم
# ==========================================
st.set_page_config(
    page_title="روبوت الإشارات - Trading Signals",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت إشارات التداول الفنية")
st.markdown("---")

# ==========================================
# 2. القائمة الجانبية (الشريط الجانبي)
# ==========================================
st.sidebar.header("⚙️ إعدادات التحليل")

SYMBOL = st.sidebar.text_input("رمز الزوج/السهم (مثل EURUSD=X أو AAPL):", value="EURUSD=X")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني (Timeframe):", ["1d", "1h", "15m", "5m"], index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("إعدادات المؤشرات")
AO_FAST = st.sidebar.number_input("فترة AO السريعة:", min_value=1, value=5)
AO_SLOW = st.sidebar.number_input("فترة AO البطيئة:", min_value=1, value=34)
SIGNAL_WMA = st.sidebar.number_input("فترة إشارة WMA:", min_value=1, value=5)

# ==========================================
# 3. دالة جلب البيانات وتحليلها
# ==========================================
def fetch_and_analyze_data(symbol, timeframe):
    try:
        # جلب البيانات من yfinance
        df = yf.download(symbol, period="1y", interval=timeframe, progress=False)
        
        if df.empty:
            return None
        
        # معالجة الأعمدة المتعددة (MultiIndex) لتعمل مع الإصدارات الحديثة من yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # التأكد من أن عمود الإغلاق هو Series ذو بعد واحد
        close_series = df['Close'].squeeze()
        
        # 1. حساب مؤشر GO Strategy (Awesome Oscillator)
        sma_fast = ta.sma(close_series, length=AO_FAST)
        sma_slow = ta.sma(close_series, length=AO_SLOW)
        
        df['sma_fast'] = sma_fast
        df['sma_slow'] = sma_slow
        df['buffer1'] = sma_fast - sma_slow
        df['buffer2'] = ta.wma(df['buffer1'], length=SIGNAL_WMA)
        
        # 2. توليد إشارات التداول
        df['Signal'] = 0
        
        # إشارة شراء (Buy Signal)
        buy_condition = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
        df.loc[buy_condition, 'Signal'] = 1
        
        # إشارة بيع (Sell Signal)
        sell_condition = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
        return None

# ==========================================
# 4. عرض النتائج والتنبيهات
# ==========================================
with st.spinner('جاري جلب البيانات وتحليلها...'):
    data = fetch_and_analyze_data(SYMBOL, TIMEFRAME)

if data is None or data.empty:
    st.error("❌ تعذر جلب البيانات. تأكد من صحة رمز الزوج (مثال: EURUSD=X أو AAPL أو BTC-USD).")
else:
    # الحصول على أحدث شمعة وأحدث إشارة
    latest_row = data.iloc[-1]
    last_signal = latest_row['Signal']
    current_price = latest_row['Close']
    
    # عرض ملخص السعر
    col1, col2, col3 = st.columns(3)
    col1.metric("الرمز", SYMBOL)
    col2.metric("السعر الحالي", f"{current_price:.4f}" if isinstance(current_price, float) else str(current_price))
    
    # عرض حالة الإشارة الحالية
    if last_signal == 1:
        col3.success("🟢 إشارة شراء (BUY)")
    elif last_signal == -1:
        col3.error("🔴 إشارة بيع (SELL)")
    else:
        col3.info("⚪ لا توجد إشارة جديدة (NEUTRAL)")

    st.markdown("---")

    # عرض جدول بالإشارات الأخيرة
    st.subheader("📋 سجل أحدث الإشارات")
    signals_df = data[data['Signal'] != 0][['Close', 'buffer1', 'buffer2', 'Signal']].tail(10)
    
    # تحسين عرض قيم الإشارة
    signals_df['نوع الإشارة'] = signals_df['Signal'].map({1: '🟢 شراء', -1: '🔴 بيع'})
    st.dataframe(signals_df[['Close', 'buffer1', 'buffer2', 'نوع الإشارة']], use_container_width=True)

    # رسم البياني المؤشر
    st.subheader("📊 الرسم البياني للمؤشر")
    st.line_chart(data[['buffer1', 'buffer2']].tail(100))
