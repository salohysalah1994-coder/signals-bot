import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import time

# ==========================================
# 1. إعدادات الصفحة والتصاميم
# ==========================================
st.set_page_config(
    page_title="روبوت الإشارات - Trading Signals",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت إشارات التداول (كل 5 دقائق)")
st.markdown("---")

# ==========================================
# 2. القائمة الجانبية (الشريط الجانبي)
# ==========================================
st.sidebar.header("⚙️ إعدادات التحليل")

SYMBOL = st.sidebar.text_input("رمز الزوج/السهم (مثل EURUSD=X أو BTC-USD):", value="EURUSD=X")

# اختيار الإطار الزمني - افتراضياً 5m
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني (Timeframe):", ["5m", "1m", "15m", "1h", "1d"], index=0)

# إضافة زر تفعيل التحديث التلقائي
AUTO_REFRESH = st.sidebar.checkbox("🔄 تفعيل التحديث التلقائي كل 5 دقائق", value=True)

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
        # تحديد فترة جلب البيانات بناءً على الفريم
        period = "7d" if timeframe in ["1m", "5m", "15m"] else "1y"
        
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)
        
        if df.empty:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
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
        
        buy_condition = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
        df.loc[buy_condition, 'Signal'] = 1
        
        sell_condition = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
        return None

# ==========================================
# 4. عرض النتائج والتنبيهات
# ==========================================
data = fetch_and_analyze_data(SYMBOL, TIMEFRAME)

if data is None or data.empty:
    st.error("❌ تعذر جلب البيانات. تأكد من صحة رمز الزوج (مثال: EURUSD=X أو BTC-USD).")
else:
    latest_row = data.iloc[-1]
    last_signal = latest_row['Signal']
    current_price = latest_row['Close']
    
    col1, col2, col3 = st.columns(3)
    col1.metric("الرمز / الفريم", f"{SYMBOL} ({TIMEFRAME})")
    col2.metric("السعر الحالي", f"{current_price:.4f}" if isinstance(current_price, float) else str(current_price))
    
    if last_signal == 1:
        col3.success("🟢 إشارة شراء جديدة (BUY)")
    elif last_signal == -1:
        col3.error("🔴 إشارة بيع جديدة (SELL)")
    else:
        col3.info("⚪ لا توجد إشارة جديدة (محايد)")

    st.markdown("---")

    st.subheader("📋 أحدث 5 صفقات / إشارات تم رصدها")
    signals_df = data[data['Signal'] != 0][['Close', 'buffer1', 'buffer2', 'Signal']].tail(5)
    signals_df['نوع الإشارة'] = signals_df['Signal'].map({1: '🟢 شراء', -1: '🔴 بيع'})
    st.dataframe(signals_df[['Close', 'نوع الإشارة']], use_container_width=True)

    st.subheader("📊 الرسم البياني للإشارة")
    st.line_chart(data[['buffer1', 'buffer2']].tail(60))

# ==========================================
# 5. التحديث التلقائي كل 5 دقائق (300 ثانية)
# ==========================================
if AUTO_REFRESH:
    time.sleep(300)
    st.rerun()
