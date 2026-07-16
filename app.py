import streamlit as st
import pandas as pd
import numpy as np
import ta
import time
import datetime
from pocketoptionapi import PocketOptionAPI

# --- إعدادات واجهة المستخدم --- #
st.set_page_config(page_title="Pocket Option Signal Radar - Manual Trading", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stSuccess { background-color: #00ff0022; border: 1px solid #00ff00; }
    .stError { background-color: #ff000022; border: 1px solid #ff0000; }
    .stWarning { background-color: #ffc10722; border: 1px solid #ffc107; }
    h1, h3 { color: #00ff00; }
    a { color: cyan; text-decoration: none; }
    a:hover { color: #00ffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("📡 رادار إشارات Pocket Option - للتداول اليدوي")
st.write("هذا التطبيق يحلل السوق ويعرض لك إشارات شراء/بيع بناءً على استراتيجية RSI + Stochastic.")

# --- إعدادات الاتصال بالمنصة (يجب تعديلها) --- #
# للحصول على الـ SSID: افتح Pocket Option في المتصفح، F12 -> Application -> Cookies -> ابحث عن 'ssid'
# لا تشارك الـ SSID الخاص بك! يفضل استخدام Streamlit Secrets أو متغيرات البيئة.
SSID = st.secrets.get("POCKET_OPTION_SSID", "ضع_الـ_SSID_الخاص_بك_هنا")

@st.cache_resource
def connect_to_pocket_option(ssid):
    if ssid == "ضع_الـ_SSID_الخاص_بك_هنا" or not ssid:
        st.error("⚠️ يرجى إدخال الـ SSID الخاص بك في إعدادات Streamlit Secrets أو مباشرة في الكود.")
        return None
    try:
        api = PocketOption(ssid)
        api.connect()
        if api.check_connect():
            st.success("✅ تم الاتصال بمنصة Pocket Option بنجاح! 🟢")
            return api
        else:
            st.error("❌ فشل الاتصال بمنصة Pocket Option. تأكد من صحة الـ SSID.")
            return None
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء الاتصال: {e}")
        return None

api = connect_to_pocket_option(SSID)

# --- إعدادات الاستراتيجية من الشريط الجانبي --- #
st.sidebar.header("🛠️ ضبط الإعدادات")
selected_pair = st.sidebar.selectbox("الزوج الرسمي", ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"])
selected_frame_str = st.sidebar.selectbox("فريم الشمعة", ["1 Minute", "5 Minutes"])
expiry_time_str = st.sidebar.selectbox("مدة الصفقة الموصى بها", ["2 Minutes", "3 Minutes", "5 Minutes"])

# تحويل الفريم الزمني ومدة الانتهاء إلى ثوانٍ
timeframe_seconds = 60 if selected_frame_str == "1 Minute" else 300
expiry_seconds = int(expiry_time_str.split(" ")[0]) * 60

# --- جلب البيانات الحية --- #
@st.cache_data(ttl=10) # تحديث البيانات كل 10 ثوانٍ
def fetch_live_data(api_client, pair, timeframe_sec, count=100):
    if api_client is None:
        return None
    try:
        candles = api_client.get_candles(pair, timeframe_sec, count, time.time())
        if not candles:
            st.warning(f"لا توجد بيانات شموع لـ {pair} على الفريم {timeframe_sec/60} دقيقة.")
            return None
            
        df = pd.DataFrame(candles)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df.rename(columns={
            "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"
        }, inplace=True)
        return df
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء جلب البيانات: {e}")
        return None

# --- عرض الإشارات --- #
if api:
    data = fetch_live_data(api, selected_pair, timeframe_seconds)

    if data is not None and not data.empty:
        # --- حساب المؤشرات الفنية --- #
        data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()
        stoch = ta.momentum.StochasticOscillator(data["High"], data["Low"], data["Close"], window=14, smooth_window=3)
        data["K"] = stoch.stoch()
        data["D"] = stoch.stoch_signal()

        # استخراج آخر القيم
        last_rsi = data["RSI"].iloc[-1]
        last_k = data["K"].iloc[-1]
        last_d = data["D"].iloc[-1]
        current_price = data["Close"].iloc[-1]
        current_time = datetime.datetime.now().strftime("%H:%M:%S")

        st.markdown(f"<p id=\"timezone-info\">الوقت الحالي: <span id=\"current-time\">{current_time}</span></p>", unsafe_allow_html=True)
        st.markdown(f"### 📊 تحليل الزوج: {selected_pair}")

        col1, col2, col3 = st.columns(3)
        col1.metric("السعر الحالي", f"{current_price:.4f}")
        col2.metric("RSI (14)", f"{last_rsi:.2f}")
        col3.metric("Stoch K/D", f"{last_k:.1f}/{last_d:.1f}")

        st.divider()

        # --- منطق الإشارة الذهبية --- #
        st.subheader("🚀 الإشارة الحالية")

        signal_found = False
        # شروط الشراء (CALL)
        if last_rsi < 30 and last_k < 20 and last_k > last_d:
            st.success(f"✅ **إشارة شراء (CALL)**\n\n*   **زمن الدخول:** الآن ({current_time})\n*   **مدة الصفقة الموصى بها:** **{expiry_time_str}**\n*   **السبب:** تشبع بيعي قوي (RSI < 30) وتقاطع صاعد في Stochastic في منطقة التشبع البيعي (K < 20 و K > D).")
            st.balloons()
            signal_found = True

        # شروط البيع (PUT)
        elif last_rsi > 70 and last_k > 80 and last_k < last_d:
            st.error(f"🔻 **إشارة بيع (PUT)**\n\n*   **زمن الدخول:** الآن ({current_time})\n*   **مدة الصفقة الموصى بها:** **{expiry_time_str}**\n*   **السبب:** تشبع شرائي قوي (RSI > 70) وتقاطع هابط في Stochastic في منطقة التشبع الشرائي (K > 80 و K < D).")
            signal_found = True

        if not signal_found:
            st.warning("⏳ **في انتظار فرصة قوية...**\n\nالسوق حالياً في منطقة عرضية أو لا توجد إشارة واضحة. يرجى الانتظار أو تغيير الزوج/الفريم.")

        st.divider()
        st.caption("ملاحظة: هذا التطبيق يحلل البيانات الفنية لحظياً. تأكد من مطابقة الإشارة مع حركة الشموع في منصة Pocket Option. التداول ينطوي على مخاطر عالية.")

        # رسم بياني للسعر والمؤشرات (للمراقبة)
        st.subheader("📈 حركة السعر والمؤشرات")
        st.line_chart(data[["Close", "RSI", "K", "D"]])

        # تحديث تلقائي للصفحة كل 10 ثوانٍ
        time.sleep(10)
        st.experimental_rerun()

    else:
        st.warning("لا يمكن جلب البيانات. يرجى التحقق من الاتصال بالإنترنت وإعدادات الـ API.")
else:
    st.warning("يرجى التأكد من إدخال الـ SSID الصحيح والاتصال بمنصة Pocket Option.")

