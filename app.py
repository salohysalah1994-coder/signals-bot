import streamlit as st
import pandas as pd
import numpy as np
import pandas_ta as ta
import requests
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
# 2. قائمة الأزواج والعملات الرسمية + الذهب
# ==========================================
FOREX_PAIRS = [
    # الذهب
    "XAU/USD",
    # الأزواج الرئيسية (Majors)
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CHF",
    "AUD/USD",
    "USD/CAD",
    "NZD/USD",
    # الأزواج التقاطعية والفرعية (Crosses)
    "EUR/GBP",
    "EUR/JPY",
    "GBP/JPY",
    "EUR/AUD",
    "EUR/CAD",
    "GBP/CAD",
    "AUD/JPY",
    "CAD/JPY",
    "NZD/JPY",
    "GBP/AUD",
    "AUD/CAD"
]

# ==========================================
# 3. القائمة الجانبية والإعدادات
# ==========================================
st.sidebar.header("⚙️ إعدادات الزوج والحساب")

# القائمة المنسدلة لاختيار الزوج أو الذهب
SYMBOL = st.sidebar.selectbox("اختر الزوج / الذهب:", FOREX_PAIRS, index=1)
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني (الفريم):", ["5min", "1min", "15min"], index=0)
API_KEY = st.sidebar.text_input("مفتاح Twelve Data API Key:", value="demo", type="password")
AUTO_REFRESH = st.sidebar.checkbox("🔄 تفعيل التحديث التلقائي كل دقيقة", value=True)

# تحديد مدة الصفقة بالدقائق بناءً على الفريم
duration_map = {"1min": 1, "5min": 5, "15min": 15}
trade_duration = duration_map.get(TIMEFRAME, 5)

# ==========================================
# 4. دالة جلب الأسعار وحساب التوقيت
# ==========================================
def fetch_twelvedata(symbol, interval, api_key):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={api_key}"
        response = requests.get(url).json()
        
        if "values" not in response:
            st.error(f"خطأ في جلب بيانات ({symbol}): {response.get('message', 'تأكد من اختيار زوج يدعمه المفتاح أو ادخل مفتاح API خاص بك')}")
            return None
        
        df = pd.DataFrame(response['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
            
        close_series = df['close']
        
        # حساب المؤشرات (SMA & RSI)
        sma_fast = ta.sma(close_series, length=5)
        sma_slow = ta.sma(close_series, length=34)
        df['buffer1'] = sma_fast - sma_slow
        df['buffer2'] = ta.wma(df['buffer1'], length=5)
        df['rsi'] = ta.rsi(close_series, length=14)
        
        # تحديد الإشارات المفلترة
        df['Signal'] = 0
        raw_buy = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
        raw_sell = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))
        
        df.loc[raw_buy & (df['rsi'] > 50), 'Signal'] = 1
        df.loc[raw_sell & (df['rsi'] < 50), 'Signal'] = -1
        
        return df
    except Exception as e:
        st.error(f"حدث خطأ في الاتصال: {e}")
        return None

# ==========================================
# 5. عرض البيانات والتوجيهات على الشاشة
# ==========================================
data = fetch_twelvedata(SYMBOL, TIMEFRAME, API_KEY)

if data is not None and not data.empty:
    latest = data.iloc[-1]
    current_price = latest['close']
    current_rsi = latest['rsi']
    last_signal = latest['Signal']
    last_time = latest['datetime']
    
    # حساب وقت بداية الشمعة التالية بالدقيقة
    next_entry_time = last_time + timedelta(minutes=trade_duration)
    entry_time_str = next_entry_time.strftime('%H:%M:%S')
    
    col1, col2, col3 = st.columns(3)
    col1.metric("الرمز المختار", f"{SYMBOL} ({TIMEFRAME})")
    col2.metric("السعر الحي المباشر", f"{current_price:.5f}" if "USD" in SYMBOL and "JPY" not in SYMBOL else f"{current_price:.2f}")
    col3.metric("مؤشر RSI", f"{current_rsi:.1f}" if pd.notnull(current_rsi) else "N/A")
    
    st.markdown("---")
    
    # عرض توصيات ووقت الدخول المحددة
    if last_signal == 1:
        st.success(f"🟢 **إشارة شراء مفلترة (BUY) لـ {SYMBOL}**")
        st.info(
            f"🎯 **تعليمات الدخول الدقيقة:**\n\n"
            f"* **توقيت الدخول:** ادخل صفقة شراء **عند الدقيقة `{entry_time_str}` بالضبط** (افتتاح الشمعة التالية).\n"
            f"* **مدة الصفقة:** اضبط المؤقت في المنصة على **`{trade_duration} دقائق`**."
        )
    elif last_signal == -1:
        st.error(f"🔴 **إشارة بيع مفلترة (SELL) لـ {SYMBOL}**")
        st.info(
            f"🎯 **تعليمات الدخول الدقيقة:**\n\n"
            f"* **توقيت الدخول:** ادخل صفقة بيع **عند الدقيقة `{entry_time_str}` بالضبط** (افتتاح الشمعة التالية).\n"
            f"* **مدة الصفقة:** اضبط المؤقت في المنصة على **`{trade_duration} دقائق`**."
        )
    else:
        st.warning(
            f"⚪ **لا توجد إشارة جديدة على {SYMBOL} حالياً**\n\n"
            f"يمكنك تغيير الزوج من القائمة الجانبية أو الانتظار حتى تتغير الإشارة."
        )
        
    st.markdown("---")
    st.subheader(f"📋 سجل الإشارات الأخيرة لـ {SYMBOL}")
    signals_df = data[data['Signal'] != 0][['datetime', 'close', 'rsi', 'Signal']].tail(5)
    if not signals_df.empty:
        signals_df['نوع الإشارة'] = signals_df['Signal'].map({1: '🟢 شراء', -1: '🔴 بيع'})
        st.dataframe(signals_df[['datetime', 'close', 'rsi', 'نوع الإشارة']], use_container_width=True)

# ==========================================
# 6. التحديث التلقائي
# ==========================================
if AUTO_REFRESH:
    time.sleep(60)
    st.rerun()
