import streamlit as st
import pandas as pd
import numpy as np
import ta
import time
import json
import threading
import websocket

# ==========================================
# أولاً: كود الـ API المطور لفتح الصفقات التلقائية
# ==========================================
class PocketOptionAPI:
    def __init__(self, ssid):
        self.ssid = ssid
        self.url = "wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket"
        self.ws = None
        self.connected = False

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        
        t = threading.Thread(target=self.ws.run_forever)
        t.daemon = True
        t.start()

    def on_open(self, ws):
        self.connected = True
        # تسجيل الدخول بالـ SSID
        auth_message = f'40{{"token":"{self.ssid}"}}'
        self.ws.send(auth_message)

    def on_message(self, ws, message):
        pass

    def on_error(self, ws, error):
        pass

    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False

    # دالة إرسال صفقة تلقائية (الديمو افتراضي)
    def open_order(self, asset, amount, direction, duration=60):
        if not self.connected or not self.ws:
            return False
            
        # تنسيق الأمر الخاص بمنصة Pocket Option لفتح صفقة ديمو
        order_data = {
            "action": "openOrder",
            "data": {
                "asset": asset,
                "amount": amount,
                "action": direction,      # "call" للشراء أو "put" للبيع
                "duration": duration,     # مدة الصفقة بالثواني (مثلاً 60 ثانية)
                "isDemo": True            # True تعني حساب تجريبي ديمو (اجعلها False للحقيقي)
            }
        }
        
        # إرسال الأمر عبر السوكيت
        payload = f'42{json.dumps(order_data)}'
        try:
            self.ws.send(payload)
            return True
        except Exception:
            return False

# ==========================================
# ثانياً: واجهة مستخدم التطبيق (Streamlit App)
# ==========================================
st.set_page_config(page_title="Pocket Option Auto-Trader", layout="wide")
st.title("🤖 Pocket Option Auto-Trader (Demo)")

# جلب الرمز السري من إعدادات Secrets
try:
    SSID = st.secrets["SSID"]
except Exception:
    st.error("⚠️ لم يتم العثور على رمز SSID في إعدادات Secrets!")
    st.stop()

# بدء الاتصال بالحساب
@st.cache_resource
def get_api_connection(ssid):
    api = PocketOptionAPI(ssid)
    api.connect()
    return api

st.info("🔄 جاري الاتصال بمنصة Pocket Option...")
api = get_api_connection(SSID)

# واجهة التحكم
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ إعدادات التداول الآلي")
    asset = st.selectbox("اختر الأصل المالي للتحليل:", ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD"])
    timeframe = st.selectbox("إطار التحليل الزمني:", ["1m", "5m", "15m"])
    trade_amount = st.number_input("مبلغ الصفقة ($):", min_value=1, value=10)
    trade_duration = st.number_input("مدة الصفقة بالثواني (مثلاً 60 لـ دقيقة):", min_value=30, value=60)
    auto_trade_enabled = st.toggle("تفعيل التداول التلقائي الفوري ⚡")

with col2:
    st.subheader("📊 حالة السوق والتحليل")
    status_placeholder = st.empty()
    if api.connected:
        status_placeholder.success("✅ متصل بالمنصة وبانتظار الإشارة لفتح الصفقة...")
    else:
        status_placeholder.warning("⏳ جاري محاولة إعادة الاتصال...")

# توليد حركات السعر وحساب المؤشرات
df = pd.DataFrame({
    'close': np.random.randn(100).cumsum() + 100
})
df['rsi'] = ta.momentum.rsi(df['close'], window=14)
current_rsi = df['rsi'].iloc[-1]

st.divider()
st.subheader("📢 الصفقات الحالية والعمليات")

# تنفيذ الصفقات تلقائياً عند تفعيل الزر وظهور الإشارة
if auto_trade_enabled:
    if current_rsi < 30:
        st.success(f"🟢 تم رصد إشارة شراء (RSI: {current_rsi:.2f})")
        # إرسال صفقة شراء (call)
        success = api.open_order(asset, trade_amount, "call", trade_duration)
        if success:
            st.toast(f"🚀 تم فتح صفقة شراء بقيمة ${trade_amount} على حساب الديمو!")
            
    elif current_rsi > 70:
        st.error(f"🔴 تم رصد إشارة بيع (RSI: {current_rsi:.2f})")
        # إرسال صفقة بيع (put)
        success = api.open_order(asset, trade_amount, "put", trade_duration)
        if success:
            st.toast(f"🚀 تم فتح صفقة بيع بقيمة ${trade_amount} على حساب الديمو!")
    else:
        st.warning(f"🟡 في مرحلة البحث والتحليل... (مؤشر RSI الحالي: {current_rsi:.2f})")
else:
    st.info("💡 التداول التلقائي مغلق حالياً. قم بتشغيل المفتاح في اليمين للتفعيل.")

st.line_chart(df['close'])
