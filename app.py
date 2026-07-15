import streamlit as st
import pandas as pd
import ta
import time
from pocketoptionapi.stable_api import PocketOption

# --- إعدادات الاتصال بالمنصة ---
# ضع الـ SSID الذي نسخته هنا (يفضل وضعه في ملف .env للأمان)
SSID = "ضع_الـ_SSID_الخاص_بك_هنا"

@st.cache_resource
def connect_to_pocket_option():
    api = PocketOption(SSID)
    api.connect()
    # التأكد من نجاح الاتصال
    if api.check_connect():
        return api
    else:
        st.error("فشل الاتصال بمنصة Pocket Option. تأكد من صحة الـ SSID.")
        return None

api = connect_to_pocket_option()

# --- جلب البيانات الحية ---
def fetch_live_data(api, pair, timeframe_seconds, count=100):
    if api is None:
        return None
    
    # جلب الشموع التاريخية
    candles = api.get_candles(pair, timeframe_seconds, count, time.time())
    
    if not candles:
        return None
        
    # تحويل البيانات إلى DataFrame
    df = pd.DataFrame(candles)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
    return df

# --- واجهة التطبيق ---
st.title("رادار إشارات بوكيت أوبشن (بيانات حية)")

if api:
    st.success("تم الاتصال بمنصة Pocket Option بنجاح! 🟢")
    
    pair = st.selectbox("اختر الزوج", ["EURUSD", "GBPUSD", "USDJPY"])
    # 60 ثانية = 1 دقيقة
    df = fetch_live_data(api, pair, 60)
    
    if df is not None:
        # حساب المؤشرات
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
        df['K'] = stoch.stoch()
        df['D'] = stoch.stoch_signal()
        
        last_rsi = df['RSI'].iloc[-1]
        last_k = df['K'].iloc[-1]
        last_d = df['D'].iloc[-1]
        
        st.write(f"السعر الحالي لـ {pair}: {df['Close'].iloc[-1]}")
        st.write(f"RSI: {last_rsi:.2f} | Stoch K: {last_k:.2f}")
        
        # منطق الإشارة
        if last_rsi < 30 and last_k < 20 and last_k > last_d:
            st.success("🟢 إشارة شراء (CALL)")
            # كود تنفيذ الصفقة تلقائياً (اختياري وخطير)
            # api.buy(1, pair, "call", 1) # شراء بـ 1 دولار لمدة دقيقة
        elif last_rsi > 70 and last_k > 80 and last_k < last_d:
            st.error("🔴 إشارة بيع (PUT)")
            # api.buy(1, pair, "put", 1)
        else:
            st.info("انتظر فرصة...")
            
        st.line_chart(df['Close'])
        
