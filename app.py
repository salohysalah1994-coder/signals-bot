import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pandas_ta as ta
import time
from datetime import datetime, timedelta

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="روبوت الإشارات الفورية - جميع الأزواج والذهب",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ روبوت الإشارات الفورية (جميع الأزواج والذهب)")
st.markdown("---")

# ==========================================
# 2. قائمة الأزواج المتاحة بدون API Key
# ==========================================
PAIRS_MAP = {
    "الذهب (XAU/USD)": "GC=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/CAD": "EURCAD=X",
    "GBP/CAD": "GBPCAD=X",
    "AUD/JPY": "AUDJPY=X"
}

# ==========================================
# 3. القائمة الجانبية
# ==========================================
st.sidebar.header("⚙️ إعدادات الزوج والحساب")

selected_pair_name = st.sidebar.selectbox("اختر الزوج / الذهب:", list(PAIRS_MAP.keys()), index=1)
SYMBOL = PAIRS_MAP[selected_pair_name]

TIMEFRAME = st.sidebar.selectbox("الإطار الزمني (الفريم):", ["5m", "1m", "15m"], index=0)
AUTO_REFRESH = st.sidebar.checkbox("🔄 تفعيل التحديث التلقائي كل دقيقة", value=True)

# تحديد مدة الصفقة بناءً على الفريم
duration_map = {"1m": 1, "5m": 5, "15m": 15}
trade_duration = duration_map.get(TIMEFRAME, 5)

# ==========================================
# 4. دالة جلب البيانات والتحليل
# ==========================================
def fetch_and_analyze(symbol, timeframe):
    try:
        df = yf.download(symbol, period="5d", interval=timeframe, progress=False)
        
        if df.empty:
            return None
            
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.reset_index()
        time_col = 'Datetime' if 'Datetime' in df.columns else 'Date'
        df['datetime'] = pd.to_datetime(df[time_col])
        
        close_series = df['Close'].squeeze()
        
        # المؤشرات
        sma_fast = ta.sma(close_series, length=5)
        sma_slow = ta.sma(close_series, length=34)
        df['buffer1'] = sma_fast - sma_slow
        df['buffer2'] = ta.wma(df['buffer1'], length=5)
        df['rsi'] = ta.rsi(close_series, length=14)
        
        # الإشارات
        df['Signal'] = 0
        raw_buy = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
        raw_sell = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))
        
        df.loc[raw_buy & (df['rsi'] > 50), 'Signal'] = 1
        df.loc[raw_sell & (df['rsi'] < 50), 'Signal'] = -1
        
        return df
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None

# ==========================================
# 5. عرض البيانات والتوجيهات
# ==========================================
data = fetch_and_analyze(SYMBOL, TIMEFRAME)

if data is not None and not data.empty:
    latest = data.iloc[-1]
    current_price = latest['Close']
    current_rsi = latest['rsi']
    last_signal = latest['Signal']
    last_time = latest['datetime']
    
    # حساب وقت الدخول بالدقيقة للشمعة التالية
    next_entry_time = last_time + timedelta(minutes=trade_duration)
    entry_time_str = next_entry_time.strftime('%H:%M:%S')
    
    col1, col2, col3 = st.columns(3)
    col1.metric("الزوج المختار", f"{selected_pair_name} ({TIMEFRAME})")
    col2.metric("السعر الحالي", f"{current_price:.5f}" if "JPY" not in SYMBOL and "GC" not in SYMBOL else f"{current_price:.2f}")
    col3.metric("مؤشر RSI", f"{current_rsi:.1f}" if pd.notnull(current_rsi) else "N/A")
    
    st.markdown("---")
    
    if last_signal == 1:
        st.success(f"🟢 **إشارة شراء مفلترة (BUY) لـ {selected_pair_name}**")
        st.info(
            f"🎯 **تعليمات الدخول الدقيقة:**\n\n"
            f"* **توقيت الدخول:** ادخل صفقة شراء **عند الدقيقة `{entry_time_str}` بالضبط** (مع افتتاح الشمعة التالية).\n"
            f"* **مدة الصفقة:** اضبط المؤقت في المنصة على **`{trade_duration} دقائق`**."
        )
    elif last_signal == -1:
        st.error(f"🔴 **إشارة بيع مفلترة (SELL) لـ {selected_pair_name}**")
        st.info(
            f"🎯 **تعليمات الدخول الدقيقة:**\n\n"
            f"* **توقيت الدخول:** ادخل صفقة بيع **عند الدقيقة `{entry_time_str}` بالضبط** (مع افتتاح الشمعة التالية).\n"
            f"* **مدة الصفقة:** اضبط المؤقت في المنصة على **`{trade_duration} دقائق`**."
        )
    else:
        st.warning(
            f"⚪ **لا توجد إشارة جديدة على {selected_pair_name} حالياً**\n\n"
            f"يمكنك تغيير الزوج من القائمة الجانبية أو الانتظار حتى تتغير الإشارة."
        )
        
    st.markdown("---")
    st.subheader(f"📋 سجل الإشارات الأخيرة لـ {selected_pair_name}")
    signals_df = data[data['Signal'] != 0][['datetime', 'Close', 'rsi', 'Signal']].tail(5)
    if not signals_df.empty:
        signals_df['نوع الإشارة'] = signals_df['Signal'].map({1: '🟢 شراء', -1: '🔴 بيع'})
        st.dataframe(signals_df[['datetime', 'Close', 'rsi', 'نوع الإشارة']], use_container_width=True)

# ==========================================
# 6. التحديث التلقائي
# ==========================================
if AUTO_REFRESH:
    time.sleep(60)
    st.rerun()
