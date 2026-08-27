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
    page_title="روبوت الإشارات الفورية - التوقيت المباشر",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ روبوت الإشارات الفورية (مع توقيت الدخول الدقيق)")
st.markdown("---")

# ==========================================
# 2. القائمة الجانبية والإعدادات
# ==========================================
st.sidebar.header("⚙️ إعدادات الحساب والزوج")

API_KEY = st.sidebar.text_input("مفتاح Twelve Data API Key:", value="demo", type="password")
SYMBOL = st.sidebar.text_input("رمز الزوج (مثل EUR/USD):", value="EUR/USD")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني (الفريم):", ["5min", "1min", "15min"], index=0)
AUTO_REFRESH = st.sidebar.checkbox("🔄 تفعيل التحديث التلقائي كل دقيقة", value=True)

# تحديد مدة الصفقة بالدقائق بناءً على الفريم
duration_map = {"1min": 1, "5min": 5, "15min": 15}
trade_duration = duration_map.get(TIMEFRAME, 5)

# ==========================================
# 3. دالة جلب الأسعار وحساب التوقيت
# ==========================================
def fetch_twelvedata(symbol, interval, api_key):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={api_key}"
        response = requests.get(url).json()
        
        if "values" not in response:
            st.error(f"خطأ في جلب البيانات: {response.get('message', 'تأكد من رمز الزوج ومفتاح API')}")
            return None
        
        df = pd.DataFrame(response['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
            
        close_series = df['close']
        
        # حساب المؤشرات
        sma_fast = ta.sma(close_series, length=5)
        sma_slow = ta.sma(close_series, length=34)
        df['buffer1'] = sma_fast - sma_slow
        df['buffer2'] = ta.wma(df['buffer1'], length=5)
        df['rsi'] = ta.rsi(close_series, length=14)
        
        # تحديد الإشارات
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
# 4. عرض الشاشة والتوجيه الصريح
# ==========================================
data = fetch_twelvedata(SYMBOL, TIMEFRAME, API_KEY)

if data is not None and not data.empty:
    latest = data.iloc[-1]
    current_price = latest['close']
    current_rsi = latest['rsi']
    last_signal = latest['Signal']
    last_time = latest['datetime']
    
    # حساب وقت الدخول للشمعة الجديدة (بداية الشمعة التالية)
    next_entry_time = last_time + timedelta(minutes=trade_duration)
    entry_time_str = next_entry_time.strftime('%H:%M:%S')
    
    col1, col2, col3 = st.columns(3)
    col1.metric("الزوج / الفريم", f"{SYMBOL} ({TIMEFRAME})")
    col2.metric("السعر الحي المباشر", f"{current_price:.5f}")
    col3.metric("مؤشر RSI", f"{current_rsi:.1f}" if pd.notnull(current_rsi) else "N/A")
    
    st.markdown("---")
    
    # عرض تعليمات الدخول الواضحة
    if last_signal == 1:
        st.success(f"🟢 **إشارة شراء (BUY)**")
        st.alert_tile = st.info(
            f"🎯 **تعليمات الدخول:**\n\n"
            f"* **وقت الدخول:** ادخل صفقة شراء **عند الدقيقة `{entry_time_str}` بالضبط** (أول ثانية من الشمعة).\n"
            f"* **مدة الصفقة:** اضبط المؤقت في المنصة على **`{trade_duration} دقائق`**."
        )
    elif last_signal == -1:
        st.error(f"🔴 **إشارة بيع (SELL)**")
        st.info(
            f"🎯 **تعليمات الدخول:**\n\n"
            f"* **وقت الدخول:** ادخل صفقة بيع **عند الدقيقة `{entry_time_str}` بالضبط** (أول ثانية من الشمعة).\n"
            f"* **مدة الصفقة:** اضبط المؤقت في المنصة على **`{trade_duration} دقائق`**."
        )
    else:
        st.warning(
            f"⚪ **لا توجد إشارة جديدة حالياً**\n\n"
            f"يرجى الانتظار وعدم دخول أي صفقة حتى تتغير الحالة."
        )
        
    st.markdown("---")
    st.subheader("📋 سجل الإشارات المفلترة")
    signals_df = data[data['Signal'] != 0][['datetime', 'close', 'rsi', 'Signal']].tail(5)
    if not signals_df.empty:
        signals_df['نوع الإشارة'] = signals_df['Signal'].map({1: '🟢 شراء', -1: '🔴 بيع'})
        st.dataframe(signals_df[['datetime', 'close', 'rsi', 'نوع الإشارة']], use_container_width=True)

# ==========================================
# 5. التحديث التلقائي
# ==========================================
if AUTO_REFRESH:
    time.sleep(60)
    st.rerun()
