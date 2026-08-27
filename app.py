import streamlit as st
import pandas as pd
import numpy as np
import pandas_ta as ta
import requests
import time

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="روبوت الإشارات الفورية - Twelve Data",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ روبوت الإشارات الفورية (أسعار حية)")
st.markdown("---")

# ==========================================
# 2. القائمة الجانبية
# ==========================================
st.sidebar.header("⚙️ إعدادات الحساب والزوج")

# ادخل مفتاح API الخاص بك هنا أو في الشريط الجانبي
API_KEY = st.sidebar.text_input("مفتاح Twelve Data API Key:", value="ضع_المفتاح_هنا", type="password")
SYMBOL = st.sidebar.text_input("رمز الزوج (مثل EUR/USD):", value="EUR/USD")
TIMEFRAME = st.sidebar.selectbox("الإطار الزمني:", ["5min", "1min", "15min", "1h"], index=0)
AUTO_REFRESH = st.sidebar.checkbox("🔄 تفعيل التحديث التلقائي كل دقيقة", value=True)

# ==========================================
# 3. دالة جلب الأسعار الفورية عبر Twelve Data
# ==========================================
def fetch_twelvedata(symbol, interval, api_key):
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={api_key}"
        response = requests.get(url).json()
        
        if "values" not in response:
            st.error(f"خطأ في جلب البيانات: {response.get('message', 'تأكد من رمز الزوج ومفتاح API')}")
            return None
        
        # تحويل البيانات إلى الجدول
        df = pd.DataFrame(response['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime').reset_index(drop=True)
        
        # تحويل الأسعار لأرقام عشرية
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
            
        close_series = df['close']
        
        # حساب المؤشرات
        sma_fast = ta.sma(close_series, length=5)
        sma_slow = ta.sma(close_series, length=34)
        df['buffer1'] = sma_fast - sma_slow
        df['buffer2'] = ta.wma(df['buffer1'], length=5)
        df['rsi'] = ta.rsi(close_series, length=14)
        
        # الشروط والإشارات
        df['Signal'] = 0
        raw_buy = (df['buffer1'] > df['buffer2']) & (df['buffer1'].shift(1) <= df['buffer2'].shift(1))
        raw_sell = (df['buffer1'] < df['buffer2']) & (df['buffer1'].shift(1) >= df['buffer2'].shift(1))
        
        df.loc[raw_buy & (df['rsi'] > 50), 'Signal'] = 1
        df.loc[raw_sell & (df['rsi'] < 50), 'Signal'] = -1
        
        return df
    except Exception as e:
        st.error(f"حدث خطأ: {e}")
        return None

# ==========================================
# 4. عرض الشاشة والتنبيهات
# ==========================================
if API_KEY == "ضع_المفتاح_هنا" or not API_KEY:
    st.warning("⚠️ يرجى إدخال مفتاح API Key في الشريط الجانبي لبدء جلب الأسعار الحية.")
else:
    data = fetch_twelvedata(SYMBOL, TIMEFRAME, API_KEY)
    
    if data is not None and not data.empty:
        latest = data.iloc[-1]
        current_price = latest['close']
        current_rsi = latest['rsi']
        last_signal = latest['Signal']
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("الزوج / الفريم", f"{SYMBOL} ({TIMEFRAME})")
        col2.metric("السعر الحي المباشر", f"{current_price:.5f}")
        col3.metric("مؤشر RSI", f"{current_rsi:.1f}" if pd.notnull(current_rsi) else "N/A")
        
        if last_signal == 1:
            col4.success("🟢 إشارة شراء فورية (BUY)")
        elif last_signal == -1:
            col4.error("🔴 إشارة بيع فورية (SELL)")
        else:
            col4.info("⚪ لا توجد إشارة جديدة")
            
        st.markdown("---")
        st.subheader("📋 سجل الإشارات المفلترة الحية")
        signals_df = data[data['Signal'] != 0][['datetime', 'close', 'rsi', 'Signal']].tail(5)
        if not signals_df.empty:
            signals_df['نوع الإشارة'] = signals_df['Signal'].map({1: '🟢 شراء', -1: '🔴 بيع'})
            st.dataframe(signals_df[['datetime', 'close', 'rsi', 'نوع الإشارة']], use_container_width=True)
            
        st.subheader("📊 رسم البياني للزخم والتأكيد")
        st.line_chart(data[['buffer1', 'buffer2']].tail(40))

# ==========================================
# 5. التحديث التلقائي
# ==========================================
if AUTO_REFRESH and API_KEY != "ضع_المفتاح_هنا":
    time.sleep(60)
    st.rerun()
