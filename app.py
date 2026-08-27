import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import time

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="روبوت الإشارات المفلترة - Trading Signals",
    page_icon="📈",
    layout="wide"
)

st.title("📈 روبوت الإشارات الفنية (مفلتر بـ RSI)")
st.markdown("---")

# ==========================================
# 2. القائمة الجانبية
# ==========================================
st.sidebar.header("⚙️ إعدادات التحليل")

SYMBOL = st.sidebar.text_input("رمز الزوج/السهم (مثل EURUSD=X أو BTC-USD):", value="EURUSD=X")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني:", ["5m", "1m", "15m", "1h", "1d"], index=0)
AUTO_REFRESH = st.sidebar.checkbox("🔄 تفعيل التحديث التلقائي كل 5 دقائق", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("إعدادات المؤشرات والفلترة")
AO_FAST = st.sidebar.number_input("فترة AO السريعة:", min_value=1, value=5)
AO_SLOW = st.sidebar.number_input("فترة AO البطيئة:", min_value=1, value=34)
SIGNAL_WMA = st.sidebar.number_input("فترة إشارة WMA:", min_value=1, value=5)

# إعدادات RSI للفلترة
RSI_PERIOD = st.sidebar.number_input("فترة مؤشر RSI:", min_value=1, value=14)
USE_RSI_FILTER = st.sidebar.checkbox("🛡️ تفعيل فلتر RSI (تقليل الإشارات الكاذبة)", value=True)

# ==========================================
# 3. دالة جلب البيانات والتحليل المفلتر
# ==========================================
def fetch_and_analyze_data(symbol, timeframe):
    try:
        period = "7d" if timeframe in ["1m", "5m", "15m"] else "1y"
        df = yf.download(symbol, period=period, interval=timeframe, progress=False)
        
        if df.empty:
            return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        close_series = df['Close'].squeeze()
        
        # 1. حساب مؤشرات الاستراتيجية
        sma_fast = ta.sma(close_series, length=AO_FAST)
        sma_slow = ta.sma(close_series, length=AO_SLOW)
        
        df['buffer1'] = sma_fast - sma_slow
        df['buffer2'] = ta.wma(df['buffer1'], length=SIGNAL_WMA)
        
        # 2. حساب مؤشر RSI للفلترة
        df['rsi'] = ta.rsi(close_series, length=RSI_PERIOD)
        
        # 3. توليد الشروط والتقاطعات
        df['Signal'] = 0
        
        raw_buy = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
        raw_sell = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))
        
        # تطبيق الفلترة
        if USE_RSI_FILTER:
            buy_condition = raw_buy & (df['rsi'] > 50)
            sell_condition = raw_sell & (df['rsi'] < 50)
        else:
            buy_condition = raw_buy
            sell_condition = raw_sell
            
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df

    except Exception as e:
        st.error(f"حدث خطأ أثناء معالجة البيانات: {e}")
        return None

# ==========================================
# 4. عرض النتائج
# ==========================================
data = fetch_and_analyze_data(SYMBOL, TIMEFRAME)

if data is None or data.empty:
    st.error("❌ تعذر جلب البيانات. تأكد من صحة رمز الزوج.")
else:
    latest_row = data.iloc[-1]
    last_signal = latest_row['Signal']
    current_price = latest_row['Close']
    current_rsi = latest_row['rsi']
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("الرمز / الفريم", f"{SYMBOL} ({TIMEFRAME})")
    col2.metric("السعر الحالي", f"{current_price:.4f}" if isinstance(current_price, float) else str(current_price))
    col3.metric("مؤشر RSI", f"{current_rsi:.1f}" if pd.notnull(current_rsi) else "N/A")
    
    if last_signal == 1:
        col4.success("🟢 إشارة شراء مفلترة (BUY)")
    elif last_signal == -1:
        col4.error("🔴 إشارة بيع مفلترة (SELL)")
    else:
        col4.info("⚪ لا توجد إشارة جديدة")

    st.markdown("---")

    st.subheader("📋 أحدث الإشارات المفلترة")
    signals_df = data[data['Signal'] != 0][['Close', 'rsi', 'Signal']].tail(5)
    if not signals_df.empty:
        signals_df['نوع الإشارة'] = signals_df['Signal'].map({1: '🟢 شراء', -1: '🔴 بيع'})
        st.dataframe(signals_df[['Close', 'rsi', 'نوع الإشارة']], use_container_width=True)
    else:
        st.write("لا توجد إشارات حقيقية حديثة تطابق شروط الفلترة.")

    st.subheader("📊 الرسم البياني للإشارة ومؤشر RSI")
    st.line_chart(data[['buffer1', 'buffer2']].tail(60))

# ==========================================
# 5. التحديث التلقائي
# ==========================================
if AUTO_REFRESH:
    time.sleep(300)
    st.rerun()
